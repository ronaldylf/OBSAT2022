# importao dos mdulos para processamento e manipulao dos dados
from machine import (
    Pin,
    SoftI2C,
    UART,
    ADC,
    SDCard
)
import network
import urequests
#import camera
from mini_micropyGPS import MicropyGPS
from bmp280 import *
from mpu9250 import MPU9250
import rtttl, songs
import CCS811
import os
import json
import time
import base64
import sys

def now(return_seconds=False):
    # funo que retorna um objeto com os dados temporais
    # no fuso horário do estado do Maranhão (UTC-3)
    tseconds = time.time()-(3*60*60)
    if return_seconds: return tseconds
    return (time.gmtime(tseconds))

def getGPSData():
    # funo que retorna os dados do gps
    if uartGPS.any():
        c = int.from_bytes(uartGPS.read(1), "big")
        stat = gps.update(chr(c))
        return {
            "latitude": gps.latitude,
            "longitude": gps.longitude,
            "altitude": gps.altitude,
            "velocidade": gps.speed,
            "timestamp": gps.timestamp
        }

    print("error in getGPSData")
    return {"error": None}


def addMapPosition(name, latitude, longitude, session, info, icon):
    response = urequests.get(f"https://bipes.net.br/map/addMarker.php", params={
        'name': name,  # CubeSatPoincar
        'lat': latitude,
        'long': longitude,
        'session': session,
        'info': info,
        'icon': icon,
    })


def takePhoto(filename=None):
    '''
    funo retorna uma foto e armazena no
    carto SD caso seja passado o nome do arquivo
    no parmetro 'filename'
    '''
    photo = camera.capture()  # tira a foto
    if (type(filename) == str):
        file = open("fotos/"+filename+".jpg", "bw")
        file.write(photo)
        file.close()
    return photo


def batteryLevel():
    # funo que retorna o nvel da bateria em porcentagem
    adc35 = ADC(Pin(35))
    adc35.atten(ADC.ATTN_11DB)
    adc35.width(ADC.WIDTH_12BIT)
    battery_level = adc35.read()
    return round((battery_level/2600)*100, 2)


def Temperature():
    # funo que retorna a atual temperatura
    SoftI2C = SoftI2C(scl=Pin(22), sda=Pin(21))
    SoftI2C.writeto(0x40, b'\xf3')
    time.sleep_ms(70)
    t = SoftI2C.readfrom(0x40, 2)
    temperature = -46.86+175.72*(t[0]*256+t[1])/65535
    return temperature


def Pressure():
    # funo que retorna a atual presso
    bus = SoftI2C(scl=Pin(22), sda=Pin(21))
    bmp280 = BMP280(bus)
    bmp280.use_case(BMP280_CASE_WEATHER)
    bmp280.oversample(BMP280_OS_HIGH)
    bmp280.normal_measure()
    pressure = bmp280.pressure
    return pressure


def Gyro():
    # funo que retorna a atual taxa de giro nos eixos X, Y e Z
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    gyro_xyz = tuple(mpu9250s.gyro)

    return {
        'x': gyro_xyz[0],
        'y': gyro_xyz[1],
        'z': gyro_xyz[2]
    }


def Acceleration():
    # funo que retorna a atual taxa de acelerao nos eixos X, Y e Z
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    acceleration_xyz = tuple(mpu9250s.acceleration)
    return {
        'x': acceleration_xyz[0],
        'y': acceleration_xyz[1],
        'z': acceleration_xyz[2]
    }



def getData(payload={}):
    ''' 
    funo que retorna os dados dos sensores juntamente com
    o payload passado no parmetro da funo.
    '''
    data = {
        "equipe": team_id,  # id da equipe
        "bateria": batteryLevel(),
        "temperatura": Temperature(), # ok
        "pressao": Pressure(),
        "giroscopio": Gyro(),
        "acelerometro": Acceleration(),
        "payload": payload
    }
    return data

def CO2():
    bus = SoftI2C(scl=Pin(22), sda=Pin(21))
    sCCS811 = CCS811.CCS811(i2c=bus, addr=0x5A)
    ok = sCCS811.data_ready()
    return sCCS811.eCO2

def Humidity():
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    i2c.writeto(0x40,b'\xf5')
    time.sleep_ms(70)
    t = i2c.readfrom(0x40, 2)
    return -6+125*(t[0]*256+t[1])/65535

def Luminosity():
    adc34 = ADC(Pin(34))
    adc34.atten(ADC.ATTN_11DB)
    adc34.width(ADC.WIDTH_12BIT)
    light = adc34.read() #max: 4095
    return round(light, 2)


def Magnetic():
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    magnetism_xyz = tuple(mpu9250s.magnetic)

    return {
        'x': magnetism_xyz[0],
        'y': magnetism_xyz[1],
        'z': magnetism_xyz[2]
    }

# variveis editveis
url_ground_server = "http://localhost:80/sendData"
# url_icon = "https://obsat.org.br/inscricoes/n2.png",  # url do cone
url_icon = "https://i.imgur.com/nHMQQ2Y.jpeg",  # url do cone
team_id = 41  # id da equipe
session_id = 1111  # id de sesso
wifi_ssid = 'OBSAT_WIFI'  # nome da rede wifi
wifi_password = 'OBSatZenith1000'  # senha da rede wifi
# endereo na qual sero enviadas as requisies com os dados
payload_address = "http://192.168.0.1/"

# quantos minutos para cada execuo (a cada 4 minutos uma execuo)
max_delta = 4

# configurao gps
uartGPS = UART(2, tx=17, rx=16)
uartGPS.init(38400, bits=8, parity=None, stop=1)
gps = MicropyGPS()
gps.coord_format = 'dms'
print("gps OK")

# configurao microSD
#os.mount(SDCard(), '/sd')
#print("SDCard OK")

# configurao camera
#camera.init(1)
#print("camera OK")

# apagar isso depois
wifi_ssid = 'HOME'  # nome da rede wifi
wifi_password = '1234567890'  # senha da rede wifi
payload_address = "http://ptsv2.com/t/3lh3h-1651006449"

# conexo com a rede wifi
print("preparando wifi")

sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    print('conectando')
    sta_if.active(True)
    sta_if.connect(wifi_ssid, wifi_password)
    while not sta_if.isconnected(): pass

print("wifi OK")