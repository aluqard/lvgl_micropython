# Polverine 센서 예제 (BME690 + BMV080) - asyncio 버전
#
# 센서 초기화(init_sensor)와 모니터링(run)을 분리하고, 두 센서를 asyncio 태스크로
# 동시에(각자의 주기로) 폴링한다.
#
#   >>> import sensor_example
#   >>> sensor_example.main()          # 초기화 + 실행
#   # 또는 이미 asyncio 루프가 있는 앱에서:
#   >>> aq, pm = sensor_example.init_sensor()
#   >>> asyncio.create_task(sensor_example.run(aq, pm))
#
# 배선(Polverine 기본):
#   BME690  I2C0  SCL=21  SDA=14  addr=0x76
#   BMV080  SPI2  SCK=12  MOSI=11  MISO=13  CS=10

try:
    import asyncio
except ImportError:            # 구형 MicroPython 호환
    import uasyncio as asyncio

import bme690
import bmv080

# --- BME690 온도 자기발열 보정 --------------------------------------------- #
# 몇 분 안정화 후 "raw" 온도를 실제 온도계와 비교해 그 차이를 넣는다.
# 예: raw=39.5, 실온=25.0 -> 14.5
TEMP_OFFSET = 14.5

# 정확도(ACC) 사람이 읽는 라벨
ACC_LABEL = ("보정중(무시)", "낮음", "중간", "높음")


# --------------------------------------------------------------------------- #
# 초기화                                                                        #
# --------------------------------------------------------------------------- #
def init_sensor():
    """두 센서를 초기화하고 (bme690, bmv080) 객체를 반환한다.
    초기화에 실패한 센서는 None으로 반환한다."""
    aq = pm = None

    try:
        aq = bme690.BME690(scl=21, sda=14, addr=0x76, port=0,
                           mode="lp", save_state=True, temp_offset=TEMP_OFFSET)
        aq.init()
        print("BME690 초기화 완료")
    except Exception as e:
        print("BME690 초기화 실패:", e)
        aq = None

    try:
        pm = bmv080.BMV080(sck=12, mosi=11, miso=13, cs=10, host=2)
        pm.open()
        pm.configure(algorithm=bmv080.HIGH_PRECISION)
        pm.start()
        print("BMV080 초기화 완료  driver:", pm.driver_version())
    except Exception as e:
        print("BMV080 초기화 실패:", e)
        pm = None

    return aq, pm


# --------------------------------------------------------------------------- #
# 모니터링 태스크                                                               #
# --------------------------------------------------------------------------- #
async def _monitor_bme690(aq):
    while True:
        env = aq.run()
        if env:
            acc = env["iaq_accuracy"]
            print("[BME690] T {:.2f}C (raw {:.2f})  H {:.2f}% (raw {:.2f})  "
                  "P {:.2f}hPa".format(
                      env["temperature"], env["raw_temperature"],
                      env["humidity"], env["raw_humidity"],
                      env["pressure"] / 100.0))
            print("         IAQ {:.1f} [{}]  CO2 {:.1f}ppm  VOC {:.3f}ppm".format(
                env["iaq"], ACC_LABEL[acc],
                env["co2_equivalent"], env["breath_voc_equivalent"]))
            if acc == 0:
                print("         * ACC=0: IAQ/CO2/VOC는 아직 기본값(보정 진행 중)")
        # BSEC가 알려주는 다음 호출 시점까지 대기(최소 1초)
        await asyncio.sleep_ms(max(1000, aq.next_call_ms()))


async def _monitor_bmv080(pm):
    while True:
        d = pm.read()
        if d:
            print("[BMV080] PM1 {:.1f}  PM2.5 {:.1f}  PM10 {:.1f} ug/m3{}".format(
                d["pm1"], d["pm2_5"], d["pm10"],
                "  [막힘!]" if d["is_obstructed"] else ""))
        await asyncio.sleep_ms(1000)


# --------------------------------------------------------------------------- #
# 실행                                                                          #
# --------------------------------------------------------------------------- #
async def run(aq, pm):
    """초기화된 센서를 asyncio 태스크로 동시에 모니터링한다."""
    tasks = []
    if aq is not None:
        tasks.append(_monitor_bme690(aq))
    if pm is not None:
        tasks.append(_monitor_bmv080(pm))
    if not tasks:
        print("사용 가능한 센서가 없습니다.")
        return
    await asyncio.gather(*tasks)


def main():
    """초기화 후 asyncio 이벤트 루프에서 모니터링 실행(블로킹)."""
    aq, pm = init_sensor()
    print()
    try:
        asyncio.run(run(aq, pm))
    except KeyboardInterrupt:
        print("중지됨")


if __name__ == "__main__":
    main()
