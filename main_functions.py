# importao dos mdulos para processamento e manipulao dos dados
from machine import (
    Pin,
    SoftI2C,
    UART,
    ADC,
    PWM,
    SPI
)

import network
import urequests
from mini_micropyGPS import MicropyGPS
from bmp280 import *
from mpu9250 import MPU9250
import CCS811
import os
import json
import utime, time
import sys
import _thread

# variveis editveis
team_id = 41  # id da equipe
session_id = 1111  # id de sessoes
wifi_ssid = 'OBSAT_WIFI'  # nome da rede wifi
wifi_password = 'OBSatZenith1000'  # senha da rede wifi
# endereo na qual sero enviadas as requisies com os dados
payload_addresses = [
    #"http://192.168.0.1/",
    "http://ptsv2.com/t/5gwcr-1651146427/post",
    #"http://localhost:80/sendData",
]
url_icon = "https://i.imgur.com/nHMQQ2Y.jpeg",  # url do cone
max_delta = 4 # quantos minutos para cada execucao (a cada 4 minutos uma execucao)

# configuracao gps
uartGPS = UART(2, tx=17, rx=13)
uartGPS.init(9600, bits=8, parity=None, stop=1)
gps = MicropyGPS(-3, "dd") # utc-3 (fuso horário maranhense)
gpsdata = {}
time.sleep(1)
def updateGPS():
    # funcao para ficar constantemente atualizando os dados do gps
    global gpsdata
    global uartGPS
    global gps
    while True:
        if uartGPS.any():
            c = int.from_bytes(uartGPS.read(1), "big")
            stat = gps.update(chr(c))
        else:
            gpsdata['error'] = "gps not found"

_thread.start_new_thread(updateGPS, ())
print("gps OK")


# configuracao microSD
print("preparando cartao sd")
import sdcard
sd = sdcard.SDCard(SPI(2), Pin(15))
try:
    os.mount(sd, '/sd')
except:
    pass
print("SDCard OK")

# variaveis de teste (apagar após os testes)
wifi_ssid = 'kaiju'  # nome da rede wifi
wifi_password = '1234567890'  # senha da rede wifi

# conexao com a rede wifi
print("preparando wifi")

sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    print('conectando')
    sta_if.active(True)
    sta_if.connect(wifi_ssid, wifi_password)
    while not sta_if.isconnected(): pass

print("wifi OK")

def clearSDCard():
    files = os.listdir("/sd")
    for file in files:
        try:
            os.remove(f"/sd/{file}")
        except:
            # arquivos obrigatórios
            pass

def GPS():
    # funcao que retorna os dados do gps
    # latitude e longitude em graus decimais 
    # altitude em metros
    # velocidade em km/h
    # datetime em (dia, mes, ano, hora, minuto, segundo)
    gpsdata = {
        "latitude": gps.latitude,
        "longitude": gps.longitude,
        "altitude": gps.altitude,
        "velocidade": gps.speed[2],
        "datetime": tuple(list(gps.date) + list(gps.timestamp))
    }
    if gpsdata['latitude'][1]=='S': gpsdata['latitude'] = -gpsdata['latitude'][0]
    if gpsdata['longitude'][1]=='W': gpsdata['longitude'] = -gpsdata['longitude'][0]
    if 'error' in gpsdata: del gpsdata['error']
    return gpsdata

def addMapPosition(name, latitude, longitude, session, info, icon):
    params={
        'name': name,
        'lat': latitude,
        'long': longitude,
        'session': session,
        'info': info,
        'icon': icon,
    }
    url = "https://bipes.net.br/map/addMarker.php"

    params_str = f"?"
    for key in params:
        value = params[key]
        params_str += f"{key}={value}&"

    params_str = params_str[:-1]
    print(url+params_str)
    response = urequests.get(url+params_str)


# def takePhoto(filename=None):
#     '''
#     funo retorna uma foto e armazena no
#     carto SD caso seja passado o nome do arquivo
#     no parmetro 'filename'
#     '''
#     photo = camera.capture()  # tira a foto
#     if (type(filename) == str):
#         file = open("fotos/"+filename+".jpg", "bw")
#         file.write(photo)
#         file.close()
#     return photo


def batteryLevel():
    # funo que retorna o nvel da bateria em porcentagem
    adc35 = ADC(Pin(35))
    adc35.atten(ADC.ATTN_11DB)
    adc35.width(ADC.WIDTH_12BIT)
    battery_level = adc35.read()
    return round((battery_level/2600)*100, 2)


def Temperature():
    # funo que retorna a atual temperatura
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    i2c.writeto(0x40, b'\xf3')
    time.sleep_ms(70)
    t = i2c.readfrom(0x40, 2)
    temperature_ = -46.86+175.72*(t[0]*256+t[1])/65535
    return round(temperature_, 2)


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

    return gyro_xyz


def Acceleration():
    # funo que retorna a atual taxa de acelerao nos eixos X, Y e Z
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    acceleration_xyz = tuple(mpu9250s.acceleration)
    
    return acceleration_xyz

def CO2():
    # nível de CO2
    bus = SoftI2C(scl=Pin(22), sda=Pin(21))
    sCCS811 = CCS811.CCS811(i2c=bus, addr=0x5A)
    ok = sCCS811.data_ready()
    return sCCS811.eCO2

def Humidity():
    # umidade
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    i2c.writeto(0x40,b'\xf5')
    time.sleep_ms(70)
    t = i2c.readfrom(0x40, 2)
    return -6+125*(t[0]*256+t[1])/65535

def Luminosity():
    # luminosidade
    adc34 = ADC(Pin(34))
    adc34.atten(ADC.ATTN_11DB)
    adc34.width(ADC.WIDTH_12BIT)
    light = adc34.read() #max: 4095
    return round(light, 2)


def Magnetic():
    # campo magnetico
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    magnetism_xyz = tuple(mpu9250s.magnetic)

    return magnetism_xyz

def getData(payload={}):
    ''' 
    funo que retorna os dados dos sensores juntamente com
    o payload passado no parmetro da funo.
    '''
    data = {
        "equipe": team_id,  # id da equipe
        "bateria": batteryLevel(),
        "temperatura": Temperature(),
        "pressao": Pressure(),
        "giroscopio": Gyro(),
        "acelerometro": Acceleration(),
        "payload": payload
    }
    return data

def debug():
    # apenas para na linha da funcao para fins de testes
    while(True): time.sleep(5)