import network
from machine import (
    Pin,
    I2C,
    UART,
    ADC,
    SDCard
)
import urequests
import camera
import os
from mini_micropyGPS import MicropyGPS
from bmp280 import *
from mpu9250 import MPU9250
from datetime import datetime, timedelta
import json
import time


#setup gps
uartGPS = UART(2, tx=17, rx=16)
uartGPS.init(38400, bits=8, parity=None, stop=1)
gps = MicropyGPS()
gps.coord_format='dms'

def getGPSData():
    if uartGPS.any():
        c=int.from_bytes(uartGPS.read(1), "big")
        stat = gps.update(chr(c))
        return {
            "latitude": gps.latitude,
            "longitude": gps.longitude,
            "altitude": gps.altitude,
            "velocidade": gps.speed,
        }

    return {"error": None}

# setup microSD
os.mount(SDCard(), '/sd')

# setup camera
camera.init(1)

def takePhoto(filename=None):
    photo = camera.capture() # take photo
    if (type(filename)==str):
        file = open(filename+".jpg", "bw")
        file.write(photo)
        file.close()
    return photo

def batteryLevel():
    adc35=ADC(Pin(35))
    adc35.atten(ADC.ATTN_11DB)
    adc35.width(ADC.WIDTH_12BIT)
    battery_level = adc35.read()
    return battery_level

def currentTemperature():
    i2c = I2C(scl=Pin(22), sda=Pin(21))
    i2c.writeto(0x40,b'\xf3')
    time.sleep_ms(70)
    t=i2c.readfrom(0x40, 2)
    temperature = -46.86+175.72*(t[0]*256+t[1])/65535
    return temperature

def currentPressure():
    bus = I2C(scl=Pin(22), sda=Pin(21))
    bmp280 = BMP280(bus)
    bmp280.use_case(BMP280_CASE_WEATHER)
    bmp280.oversample(BMP280_OS_HIGH)
    bmp280.normal_measure()
    pressure = bmp180.temperature
    return pressure

def currentGyro():
    i2c = I2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    gyro_xyz = mpu9250s.gyro
    return list(gyro_xyz)

def currentAcceleration():
    i2c=I2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    acceleration_xyz = mpu9250s.acceleration
    return list(acceleration_xyz)


sta_if = network.WLAN(network.STA_IF); sta_if.active(True)
sta_if.scan()
sta_if.connect('“OBSAT_WIFI”','OBSatZenith1000')
payload_address = "http://192.168.0.1/"

def now():
    return (datetime.utcnow()-timedelta(hours=3))

def getData(payload={}):
    data = {
        "equipe": 41, #unique id
        "bateria": batteryLevel(),
        "temperatura": currentTemperature(),
        "pressao": currentPressure(),
        "giroscopio": currentGyro(),
        "acelerometro": currentAcceleration(),
        "payload": payload # max 90 bytes
    }
    return data

#payload rate (executions per minute)
amount_executions = 4
total_minutes = 40

start_timestamp = now().timestamp() # use later
for i in range(amount_executions):
    t0 = now()
    t = now()
    while ((t-t0)<timedelta(minutes=int(total_minutes/total_minutes))):
        t = now()
        # main loop

    current_photo = takePhoto(f"foto{i+1}")
    general_data = getData({
        "timestamp": now().timestamp(), #timestamp now
        f"foto": f"foto{i+1}",
        "gps": getGPSData(),
    })
    # archive data in microSD or send to ground
    json_data = json.dumps(general_data)
    response = urequests.post(url=payload_address, json=json_data)

print("end of mission")