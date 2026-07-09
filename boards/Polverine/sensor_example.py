# Polverine 센서 간단 예제 (BME690 + BMV080)
#
# REPL에서 값 확인용. 사람이 읽기 쉬운 형태로 출력한다.
#   >>> import sensor_example
#   >>> sensor_example.run()
#
# 배선(Polverine 기본):
#   BME690  I2C0  SCL=21  SDA=14  addr=0x76
#   BMV080  SPI2  SCK=12  MOSI=11  MISO=13  CS=10

import time
import bme690
import bmv080

# --- BME690 온도 자기발열 보정 --------------------------------------------- #
# 몇 분 안정화 후 "Traw"를 실제 온도계와 비교해 그 차이를 넣는다.
# 예: Traw=39.5, 실온=25.0 -> 14.5
TEMP_OFFSET = 14.5

# 정확도(ACC) 사람이 읽는 라벨
ACC_LABEL = ("보정중(무시)", "낮음", "중간", "높음")


def run():
    # --- 센서 초기화 ------------------------------------------------------- #
    print("BME690 / BMV080 예제 시작\n")

    aq = bme690.BME690(scl=21, sda=14, addr=0x76, port=0,
                       mode="lp", save_state=True, temp_offset=TEMP_OFFSET)
    aq.init()

    pm = bmv080.BMV080(sck=12, mosi=11, miso=13, cs=10, host=2)
    pm.open()
    pm.configure(algorithm=bmv080.HIGH_PRECISION)
    pm.start()
    print("BMV080 driver:", pm.driver_version())
    print()

    last_pm = None

    while True:
        # --- 공기질 / 환경 (BME690) --------------------------------------- #
        env = aq.run()
        if env:
            acc = env["iaq_accuracy"]
            print("[BME690]")
            print("  온도  {:6.2f} C   (raw {:.2f})".format(
                env["temperature"], env["raw_temperature"]))
            print("  습도  {:6.2f} %   (raw {:.2f})".format(
                env["humidity"], env["raw_humidity"]))
            print("  기압  {:7.2f} hPa".format(env["pressure"] / 100.0))
            print("  IAQ   {:6.1f}     정확도 {} ({})".format(
                env["iaq"], acc, ACC_LABEL[acc]))
            print("  CO2   {:6.1f} ppm   VOC {:.3f} ppm".format(
                env["co2_equivalent"], env["breath_voc_equivalent"]))
            if acc == 0:
                print("  * ACC=0: IAQ/CO2/VOC는 아직 기본값. 공기 변화를 겪으며 보정되면 올라감.")

        # --- 미세먼지 (BMV080) -------------------------------------------- #
        d = pm.read()
        if d:
            last_pm = d
        if last_pm:
            print("[BMV080]")
            print("  PM1  {:5.1f}   PM2.5 {:5.1f}   PM10 {:5.1f}  ug/m3{}".format(
                last_pm["pm1"], last_pm["pm2_5"], last_pm["pm10"],
                "  [막힘!]" if last_pm["is_obstructed"] else ""))

        print("-" * 44)
        time.sleep_ms(max(1000, aq.next_call_ms()))


if __name__ == "__main__":
    run()
