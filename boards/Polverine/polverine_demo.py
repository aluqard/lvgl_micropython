# Polverine environmental-sensor demo (MicroPython)
#
# Re-implements BlackIoT's POLVERINE_DEMO
# (https://github.com/BlackIoT/Polverine/tree/main/POLVERINE_DEMO) on top of the
# built-in `bmv080` and `bme690` C modules.
#
# It streams one JSON object per line over the USB REPL, using the same
# {"topic": ..., "data": {...}} shape as the original firmware so the existing
# Node-RED flow can consume it unchanged:
#
#   {"topic": "bme690", "data": {"ID": "...", "R": 12345, "T": 24.9, "P": 1007.2,
#                                "H": 41.3, "IAQ": 63.0, "ACC": 2, "CO2": 612.0,
#                                "VOC": 0.71}}
#   {"topic": "bmv080", "data": {"ID": "...", "R": 30.0, "PM10": 8.0,
#                                "PM25": 6.0, "PM1": 5.0}}
#
# Wiring is the Polverine default:
#   BMV080  -> SPI2  SCK=12  MOSI=11  MISO=13  CS=10  (1 MHz)
#   BME690  -> I2C0  SCL=21  SDA=14   addr=0x76 (100 kHz)
#   RGB LED -> R=47  G=48  B=38  (status indicator)
#
# 실행:
#   보드에 main.py로 올리면 자동 실행되거나,
#   >>> import polverine_demo; polverine_demo.main()
#   기존 asyncio 앱에 통합:
#   >>> led, aq, pm = polverine_demo.init_sensor()
#   >>> asyncio.create_task(polverine_demo.run(led, aq, pm))

import json
import time
import machine

try:
    import asyncio
except ImportError:            # 구형 MicroPython 호환
    import uasyncio as asyncio

import bmv080
import bme690


# --------------------------------------------------------------------------- #
# Status LED (Polverine on-board RGB, driven with PWM)                          #
# --------------------------------------------------------------------------- #
class StatusLed:
    def __init__(self, r=47, g=48, b=38, active_high=True):
        self._active_high = active_high
        self._r = machine.PWM(machine.Pin(r), freq=1000, duty_u16=0)
        self._g = machine.PWM(machine.Pin(g), freq=1000, duty_u16=0)
        self._b = machine.PWM(machine.Pin(b), freq=1000, duty_u16=0)

    def _set(self, pwm, on):
        level = 13333 if on else 0   # ~1/3 brightness (was 40000)
        if not self._active_high:
            level = 65535 - level
        pwm.duty_u16(level)

    def ok(self):        # both sensors healthy -> green + blue
        self._set(self._r, False); self._set(self._g, True); self._set(self._b, True)

    def error(self):     # a sensor failed -> red
        self._set(self._r, True); self._set(self._g, False); self._set(self._b, False)


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #
def device_id():
    return "".join("{:02x}".format(b) for b in machine.unique_id())


def emit(topic, data):
    data["ID"] = DEVICE_ID
    print(json.dumps({"topic": topic, "data": data}))


DEVICE_ID = device_id()


# --------------------------------------------------------------------------- #
# Sensor setup                                                                  #
# --------------------------------------------------------------------------- #
def make_bmv080():
    s = bmv080.BMV080(sck=12, mosi=11, miso=13, cs=10, host=2, freq=1_000_000)
    s.open()
    # High precision matches the demo's air-quality use case.
    s.configure(algorithm=bmv080.HIGH_PRECISION)
    s.start()
    return s


# Self-heating offset [degC] for BSEC heat compensation. Calibrate per board:
# let the sensor run a few minutes, read "Traw", subtract the real room
# temperature, and put the difference here. e.g. Traw=39.5, room=25.0 -> 14.5.
BME690_TEMP_OFFSET = 14.5


def make_bme690():
    # Dedicated I2C port 0 (new i2c_master driver) so it never clashes with
    # a machine.I2C instance the app might create elsewhere.
    s = bme690.BME690(scl=21, sda=14, addr=0x76, port=0, freq=100_000,
                      mode="lp", save_state=True, temp_offset=BME690_TEMP_OFFSET)
    s.init()
    return s


# --------------------------------------------------------------------------- #
# 초기화                                                                        #
# --------------------------------------------------------------------------- #
def init_sensor():
    """LED + 두 센서를 초기화하고 (led, bme690, bmv080)를 반환한다.
    초기화 실패한 센서는 None으로 반환하고 LED로 상태를 표시한다."""
    led = StatusLed()
    print("# POLVERINE MicroPython demo  id={}".format(DEVICE_ID))

    aq = pm = None
    try:
        aq = make_bme690()
    except Exception as e:
        print("# BME690 init failed:", e)
    try:
        pm = make_bmv080()
    except Exception as e:
        print("# BMV080 init failed:", e)

    led.ok() if (aq is not None and pm is not None) else led.error()
    return led, aq, pm


# --------------------------------------------------------------------------- #
# 모니터링 태스크                                                               #
# --------------------------------------------------------------------------- #
async def _monitor_bme690(led, aq):
    # T / H  = BSEC heat-compensated (ambient). temp_offset 보정 시 정확.
    # Traw/Hraw = 원시값(Traw는 자기발열로 ~10-15C 높음).
    # ACC    = BSEC 정확도 0(보정중)~3. ACC==0이면 IAQ/CO2/VOC는 기본값(50/500/0.5).
    while True:
        try:
            out = aq.run()
            if out:
                emit("bme690", {
                    "R":    time.ticks_ms(),
                    "T":    round(out.get("temperature", 0.0), 2),
                    "H":    round(out.get("humidity", 0.0), 2),
                    "Traw": round(out.get("raw_temperature", 0.0), 2),
                    "Hraw": round(out.get("raw_humidity", 0.0), 2),
                    "P":    round(out.get("pressure", 0.0) / 100.0, 2),  # Pa -> hPa
                    "IAQ":  round(out.get("iaq", 0.0), 2),
                    "ACC":  out.get("iaq_accuracy", 0),
                    "CO2":  round(out.get("co2_equivalent", 0.0), 2),
                    "VOC":  round(out.get("breath_voc_equivalent", 0.0), 3),
                })
            await asyncio.sleep_ms(max(200, aq.next_call_ms()))
        except Exception as e:
            print("# BME690 read error:", e)
            led.error()
            await asyncio.sleep_ms(1000)


async def _monitor_bmv080(led, pm):
    while True:
        try:
            d = pm.read()
            if d:
                emit("bmv080", {
                    "R":    round(d["runtime"], 1),
                    "PM10": round(d["pm10"], 1),
                    "PM25": round(d["pm2_5"], 1),
                    "PM1":  round(d["pm1"], 1),
                    "OBST": 1 if d["is_obstructed"] else 0,
                })
            await asyncio.sleep_ms(1000)
        except Exception as e:
            print("# BMV080 read error:", e)
            led.error()
            await asyncio.sleep_ms(1000)


# --------------------------------------------------------------------------- #
# 실행                                                                          #
# --------------------------------------------------------------------------- #
async def run(led, aq, pm):
    """초기화된 센서를 asyncio 태스크로 동시에 모니터링한다."""
    tasks = []
    if aq is not None:
        tasks.append(_monitor_bme690(led, aq))
    if pm is not None:
        tasks.append(_monitor_bmv080(led, pm))
    if not tasks:
        print("# 사용 가능한 센서가 없습니다.")
        return
    await asyncio.gather(*tasks)


def main():
    """초기화 후 asyncio 이벤트 루프에서 데모 실행(블로킹)."""
    led, aq, pm = init_sensor()
    try:
        asyncio.run(run(led, aq, pm))
    except KeyboardInterrupt:
        print("# 중지됨")


if __name__ == "__main__":
    main()
