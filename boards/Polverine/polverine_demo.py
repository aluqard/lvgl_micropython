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
# Copy this file onto the board as main.py (or import it) to run the demo.

import json
import time
import machine

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


def run():
    led = StatusLed()
    print("# POLVERINE MicroPython demo  id={}".format(DEVICE_ID))

    pm = aq = None
    try:
        aq = make_bme690()
    except Exception as e:
        print("# BME690 init failed:", e)
    try:
        pm = make_bmv080()
    except Exception as e:
        print("# BMV080 init failed:", e)

    if pm is None or aq is None:
        led.error()
    else:
        led.ok()

    while True:
        # --- BME690 / air quality ------------------------------------------ #
        if aq is not None:
            try:
                out = aq.run()
                if out:
                    # T / H  = BSEC heat-compensated (ambient). Accurate only once
                    #          temp_offset is calibrated (see make_bme690 below).
                    # Traw/Hraw = raw sensor readings; Traw is self-heated (gas
                    #          heater warms the die) so it reads ~10-15 C high.
                    # ACC    = BSEC accuracy: 0=calibrating .. 3=calibrated. While
                    #          ACC==0, IAQ/CO2/VOC stay at BSEC defaults (50/500/0.5).
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
            except Exception as e:
                print("# BME690 read error:", e)
                led.error()

        # --- BMV080 / particulate matter ----------------------------------- #
        if pm is not None:
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
            except Exception as e:
                print("# BMV080 read error:", e)
                led.error()

        time.sleep_ms(200)


if __name__ == "__main__":
    run()
