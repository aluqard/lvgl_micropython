# BMV080 · BME690 MicroPython 빌트인 모듈 (ESP32-S3 / Polverine)

Bosch **BMV080**(미세먼지 PM1/2.5/10)과 **BME690**(온·습도·기압·가스, BSEC IAQ) 센서를
`lvgl_micropython` 펌웨어에 **빌트인 C 모듈**로 통합한 작업 기록이다.
`build_polverine.sh`로 ESP32-S3 펌웨어를 빌드하면 두 모듈이 자동으로 포함되며,
MicroPython에서 `import bmv080` / `import bme690` 로 바로 사용할 수 있다.

---

## 1. 목표

- BMV080 · BME690 벤더 SDK를 MicroPython `USER_C_MODULE`로 래핑
- ESP32-S3(Polverine)에서 동작하는 빌트인 모듈로 펌웨어에 내장
- `build_polverine.sh` 빌드 흐름에 그대로 편입
- 통신 버스: **BMV080 = SPI**, **BME690 = I2C** (C에서 ESP-IDF 직접 제어)
- BSEC 보정(IAQ) 상태를 **NVS에 영속화**

## 2. 소스 형태 (벤더 SDK)

두 SDK 모두 **아키텍처별 사전 컴파일 정적 라이브러리(`.a`) + 헤더 + 오픈소스 글루** 구조이고,
ESP32-S3용 바이너리가 이미 제공된다.

| 센서 | 사전 컴파일 lib (S3) | 헤더 | 컴파일 대상 소스 |
|------|------|------|------|
| BMV080 | `lib_bmv080.a`, `lib_postProcessor.a` (`xtensa_esp32s3`) | `bmv080.h`, `bmv080_defs.h` | (글루만 작성) |
| BME690 | `libalgobsec.a` (`esp/esp32_s3`) | `bsec_interface.h`, `bsec_datatypes.h` | `bme69x.c` (오픈소스 드라이버) |

## 3. 아키텍처

```
[Python]  import bmv080 / import bme690
   │
[MP C 래퍼]  mod_bmv080.c / mod_bme690.c   ← mp_obj 정의, MP_REGISTER_MODULE
   │
[벤더 글루]  SPI 브릿지 / I2C 브릿지(bme690_i2c_bridge) + bme69x.c
   │
[벤더 정적 lib]  lib_bmv080.a + lib_postProcessor.a  /  libalgobsec.a  (S3용)
```

`ext_mod/micropython.cmake`가 각 모듈의 `micropython.cmake`를 `ESP_PLATFORM` 가드 안에서
`include` → 빌드 시 자동으로 펌웨어에 빌트인된다.

## 4. 추가 / 변경된 파일

### 신규 (모듈 소스)
```
ext_mod/bmv080/
├── micropython.cmake              # usermod_bmv080 정의 + .a 링크(--start-group)
├── include/
│   ├── bmv080.h, bmv080_defs.h    # 벤더 헤더(복사)
├── lib/
│   ├── lib_bmv080.a, lib_postProcessor.a   # S3 사전 컴파일(복사)
└── src/
    └── mod_bmv080.c               # MP 래퍼 + SPI 콤브릿지(폴링)

ext_mod/bme690/
├── micropython.cmake              # usermod_bme690 정의 + libalgobsec.a 링크
├── include/
│   ├── bme69x.h, bme69x_defs.h
│   ├── bsec_interface.h, bsec_datatypes.h
│   ├── bme690_i2c_bridge.h
│   ├── bme690_config.h / bme690_config.c   # BSEC config blob(33v/3s LP/4d)
├── lib/
│   └── libalgobsec.a              # S3 사전 컴파일(복사)
└── src/
    ├── mod_bme690.c               # MP 래퍼 + BSEC 단일스텝 + NVS 영속화
    ├── bme690_i2c_bridge.c        # 신규 i2c_master 드라이버 브릿지
    └── bme69x.c                   # 벤더 오픈소스 드라이버(복사)
```

### 변경 (기존 파일)
- `ext_mod/micropython.cmake` — `ESP_PLATFORM` 블록에 두 모듈 `include` 추가.
  8MB 절감을 위해 `usqlite`·`micropython-ulab` include 비활성화(주석).
- `boards/Polverine/mpconfigboard.cmake` — PSRAM 비활성화(`spiram_sx`/`spiram_oct` 제거).
- `build_polverine.sh` — `--flash-size 8 --optimize-size` 플래그, 보드 복사 라인 활성화.
- `boards/Polverine/polverine_demo.py` — 신규 예제(아래 §8).

## 5. BMV080 모듈 (SPI · 폴링)

- SPI 콤브릿지는 Bosch `xtensa_esp32` 예제의 SPI 경로를 ESP-IDF `spi_master`로 이식.
  16-bit 헤더(주소 페이즈) + 16-bit 워드 페이로드, 빅→리틀 엔디안 스왑.
- **IRQ 미사용** — `read()`가 내부에서 `bmv080_serve_interrupt`를 호출하고
  `data_ready` 콜백이 채운 값을 dict로 반환(없으면 `None`).

### Python API
```python
import bmv080
s = bmv080.BMV080(sck=12, mosi=11, miso=13, cs=10, host=2, freq=1_000_000)
s.open()
s.configure(algorithm=bmv080.HIGH_PRECISION)   # FAST_RESPONSE / BALANCED / HIGH_PRECISION
s.start()
d = s.read()        # dict 또는 None
# d = {"runtime","pm1","pm2_5","pm10","pm1_number","pm2_5_number",
#      "pm10_number","is_obstructed","is_outside_measurement_range"}
s.stop(); s.close()
```
| 메서드 | 설명 |
|--------|------|
| `open()` | SPI 버스/디바이스 초기화 + 벤더 open |
| `driver_version()` | `(major, minor, patch)` |
| `configure(integration_time=, algorithm=, obstruction=, vibration=)` | 파라미터 설정(start 전) |
| `start()` / `stop()` | 연속 측정 시작/중지 |
| `read()` | 폴링 1회, 신규 샘플 dict 또는 `None` |
| `close()` / `__del__` | 종료 및 리소스 해제 |

## 6. BME690 모듈 (I2C · BSEC · NVS)

- I2C 브릿지는 ESP-IDF 5.x **신규 `i2c_master` 드라이버**로 작성 →
  MicroPython `machine.I2C`(레거시 드라이버)와 **다른 포트 번호**면 공존 가능.
- BSEC 처리 루프(Bosch `bsec_integration.c`)를 **단일 스텝 `run()`** 으로 재구성:
  매 호출마다 `bsec_sensor_control → bme69x 측정 트리거 → bme69x_get_data → bsec_do_steps`.
  벤더 예제의 파이프라인(이전 사이클 읽기 → 다음 측정 트리거) 순서를 그대로 유지.
- **NVS 영속화**: 주기적으로 `bsec_get_state`를 NVS에 저장, `init()` 시 복원 →
  재부팅 후에도 IAQ 보정 상태 유지.
- 내장 config: `bme690_iaq_33v_3s_4d`(3.3V / 3초 LP / 4일 보정). 변경 시
  `ext_mod/bme690/include/bme690_config.c`의 `bsec_config_iaq[]` 배열 교체.

### Python API
```python
import bme690, time
s = bme690.BME690(scl=21, sda=14, addr=0x76, port=0, freq=100_000,
                  mode="lp", save_state=True,   # mode: "lp" | "ulp" | "cont"
                  temp_offset=0.15)             # 선택: 자기발열 보정 오프셋[°C]
s.init()
while True:
    out = s.run()       # dict 또는 None
    if out:
        print(out["iaq"], out["iaq_accuracy"], out["co2_equivalent"],
              out["temperature"], out["humidity"], out["pressure"])
    time.sleep_ms(s.next_call_ms())
```
반환 dict 키: `iaq, iaq_accuracy, static_iaq, co2_equivalent, breath_voc_equivalent,
raw_temperature, raw_humidity, pressure, gas_resistance, temperature(보정),
humidity(보정), gas_percentage, stabilization_status, run_in_status, tvoc_equivalent(LP)`

**값 해석 주의**
- `temperature`/`humidity`는 **열 보정(heat-compensated)** 값으로, `temp_offset`(자기발열 오프셋)에
  따라 크게 달라진다. 보드에 맞게 `temp_offset`을 튜닝하지 않으면 실제 실온/습도와 어긋나
  둘이 뒤바뀐 것처럼 보일 수 있다. 직관적인 실측값이 필요하면 `raw_temperature`/`raw_humidity`를 사용.
- `breath_voc_equivalent`는 **ppm** 단위이며 청정 공기 기준선이 **≈0.5 ppm**이다(0.5 미만/근처는 정상).
  VOC 지표로 더 직관적인 값을 원하면 `gas_percentage`(%) 또는 `iaq`/`static_iaq`를 사용.
- 드라이버가 `BME69X_USE_FPU`로 컴파일되므로 bme69x 원시값은 이미 °C/%/Pa/Ω 단위(스케일 나눗셈 불필요).

| 메서드 | 설명 |
|--------|------|
| `init()` | I2C + bme69x + BSEC 초기화, NVS state 복원 |
| `run()` | BSEC 1스텝. 결과 dict 또는 `None`(아직 시점 아님) |
| `next_call_ms()` | 다음 `run()`까지 대기 시간(ms) |
| `save_state()` | BSEC state를 NVS에 강제 저장 |
| `deinit()` / `__del__` | 종료 |

## 7. 빌드 통합 (CMake)

각 `micropython.cmake`는 `spi3wire` 패턴 + 사전 컴파일 lib 링크:
```cmake
add_library(usermod_bmv080 INTERFACE)
target_sources(usermod_bmv080 INTERFACE .../mod_bmv080.c)
target_include_directories(usermod_bmv080 INTERFACE .../include)
add_library(bmv080_prebuilt STATIC IMPORTED)
set_target_properties(bmv080_prebuilt PROPERTIES IMPORTED_LOCATION .../lib_bmv080.a)
target_link_libraries(usermod_bmv080 INTERFACE
    -Wl,--start-group bmv080_prebuilt bmv080_postproc_prebuilt -Wl,--end-group)
target_link_libraries(usermod INTERFACE usermod_bmv080)
```
`ext_mod/micropython.cmake` (ESP_PLATFORM 블록):
```cmake
include(${CMAKE_CURRENT_LIST_DIR}/bmv080/micropython.cmake)
include(${CMAKE_CURRENT_LIST_DIR}/bme690/micropython.cmake)
```
사용된 ESP-IDF 컴포넌트(`driver`, `esp_timer`, `nvs_flash`, `esp_rom`)는 포트의
`idf_component_register REQUIRES`에 이미 포함 → 헤더 접근 정상.

### 빌드 중 해결한 이슈
1. `bmv080_open`/`bmv080_close` 래퍼가 벤더 심볼과 충돌 → `mp_bmv080_*`로 개명.
2. `m_new_obj_with_finaliser` 미존재(이 MP 포크) → `m_new_obj` 사용.
3. bme690 `run()`의 `data` 구조체 `-Werror=maybe-uninitialized` → `= {0}` 초기화.
4. `FROZEN_MANIFEST` 존재 검사가 보드 복사보다 먼저 실행 → 보드 사전 복사 필요
   (`build_polverine.sh`의 `cp -R boards/Polverine ...` 라인 활성화로 해결).
5. "app partition too small"은 **정상적인 1차 패스** — `make.py`가 파티션을
   자동 리사이즈해 2차 패스로 재빌드(SECOND_BUILD).

## 8. 8MB / PSRAM 없는 보드용 빌드 설정

대상 보드: **ESP32-S3, 8MB 플래시, 외장 PSRAM 없음(내부 512KB SRAM만)**.

기본 `lvgl_micropython` 앱은 ~11MB라 8MB 플래시에 들어가지 않아 크기 축소가 필요했다.

| 변경 | 방법 | 효과 |
|------|------|------|
| 플래시 8MB | `make.py ... --flash-size 8` | `CONFIG_ESPTOOLPY_FLASHSIZE_8MB` + 파티션 8MB 산정 |
| PSRAM 비활성 | `mpconfigboard.cmake`에서 `spiram_sx`/`spiram_oct` 제거 | `# CONFIG_SPIRAM is not set` (없는 PSRAM 켜서 부팅 실패 방지) |
| 크기 최적화 | `--optimize-size` | `CONFIG_COMPILER_OPTIMIZATION_SIZE`(`-Os`) |
| 폰트 축소 | 커스텀 폰트(seg14/andalemono/awesome/CJK) 비활성 | 최대 레버(수 MB) |
| 모듈 제거 | usqlite·ulab include 비활성 | ~1.7MB |

### 빌드 결과 (성공)
| 항목 | 값 |
|------|-----|
| 플래시 | 8MB |
| PSRAM | 비활성 |
| 앱 이미지 | **~3.84MB** (factory 3940K, 2576B 여유) |
| 펌웨어 | `build/lvgl_micropy_Polverine-8.bin` (~3.9MB) |
| 빌트인 모듈 | `bmv080`, `bme690` 포함 확인 |

앱이 **~11MB → ~3.84MB**로 축소, 8MB 플래시에 여유 있게 적재(나머지 ~4MB는 VFS).

### 빌드 방법
```bash
# WSL(ubuntu)에서
cd ~/lvgl_micropython_aluqard
./build_polverine.sh          # 이미 8MB / -Os / 보드복사 반영됨
```
> `build_polverine.sh` 1행의 `sudo apt-get ...`는 최초 1회 의존성 설치용.
> ccache 미사용 전체 빌드라 시간이 다소 걸린다.

### 플래시
```bash
python -m esptool --chip esp32s3 -p (PORT) -b 460800 --before default_reset --after hard_reset \
  write_flash --flash_mode dio --flash_size 8MB --flash_freq 80m --erase-all \
  0x0 build/lvgl_micropy_Polverine-8.bin
```

## 9. 예제: `boards/Polverine/polverine_demo.py`

BlackIoT `POLVERINE_DEMO`를 MicroPython으로 재현. USB REPL로 **줄 단위 JSON**을 출력해
기존 Node-RED 플로우와 호환된다.
```json
{"topic":"bme690","data":{"ID":"..","R":12345,"T":24.9,"P":1007.2,"H":41.3,"IAQ":63.0,"ACC":2,"CO2":612.0,"VOC":0.71}}
{"topic":"bmv080","data":{"ID":"..","R":30.0,"PM10":8.0,"PM25":6.0,"PM1":5.0,"OBST":0}}
```
- 상태 RGB LED(PWM): 정상=녹+청 / 오류=적. 밝기 ≈1/3(`duty_u16=13333`).
- 보드에 `main.py`로 올리면 부팅 시 자동 실행(또는 `import polverine_demo; polverine_demo.run()`).

## 10. Polverine 핀 맵

| 기능 | 신호 | GPIO |
|------|------|------|
| BMV080 SPI2 | SCK / MOSI / MISO / CS | 12 / 11 / 13 / 10 |
| BME690 I2C0 | SCL / SDA (addr 0x76) | 21 / 14 |
| 상태 LED | R / G / B | 47 / 48 / 38 |
| 부트 버튼 | — | 0 |

## 11. 알려진 제약 / 주의

- **PSRAM 없음** → MicroPython 힙이 내부 SRAM(수백 KB)으로 제한. 센서 JSON 스트리밍엔
  충분하나, 큰 LVGL 디스플레이 UI를 함께 쓰면 메모리가 빠듯할 수 있음.
- **I2C 포트 충돌 주의**: BME690는 신규 `i2c_master` 드라이버 사용. 같은 포트 번호로
  `machine.I2C`를 열지 말 것(전용 포트 권장).
- **BMV080은 연속 측정 + 폴링**만 구현(벤더 예제의 duty-cycling 미구현). 필요 시 모듈에
  `start_duty_cycling` 추가 가능.
- 벤더 정적 라이브러리(BMV080·BSEC)는 Bosch 독점 바이너리. 정적 링크는 허용되나
  소스 재배포 제한이 있으니 리포 공개 시 확인 필요.
- LED 극성(active-high/low)이 보드마다 다를 수 있음 → `StatusLed(active_high=False)`로 반전 가능.
