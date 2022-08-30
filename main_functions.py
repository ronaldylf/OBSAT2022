# importao dos modulos para processamento e manipulacao dos dados
import sdcard
from machine import (
    Pin,
    PWM,
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
import utime
import time
import sys
import _thread

# variveis editveis
team_id = 41  # id da equipe
session_id = 1111  # id de sessao para visualizacao do satelite no mapa
wifi_ssid = 'OBSAT_WIFI'  # nome da rede wifi
wifi_password = 'OBSatZenith1000'  # senha da rede wifi
# endereco na qual serao enviadas as requisicoes com os dados
payload_addresses = [
    "http://192.168.0.1/",  # sonda
    "http://161.35.3.156:33/sendData",  # endereço terrestre
]
# url do icone que aparecera no mapa
url_icon = "https://i.imgur.com/nHMQQ2Y.jpeg"
# quantos minutos para cada execucao (a cada 4 minutos uma execucao)
max_delta = 4

# configuracao gps
uartGPS = UART(2, tx=17, rx=13)
uartGPS.init(9600, bits=8, parity=None, stop=1)
gps = MicropyGPS(-3, "dd")  # utc-3 (fuso horário brasileiro)
gpsdata = {}
time.sleep(1)


def updateGPS():
    # fica constantemente atualizando os dados do gps
    while True:
        global gpsdata
        global uartGPS
        global gps
        if uartGPS.any():
            c = int.from_bytes(uartGPS.read(1), "big")
            stat = gps.update(chr(c))
        else:
            gpsdata['error'] = "gps not found"


# funciona de forma paralela, para que nao interrompa o fluxo principal do programa
_thread.start_new_thread(updateGPS, ())
print("gps OK")


# configuracao microSD
print("preparando cartao sd")
sd = sdcard.SDCard(SPI(2), Pin(15))
try:
    os.mount(sd, '/sd')
except:
    pass
print("SDCard OK")

# conexao com a rede wifi
print("preparando wifi")

sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    print('conectando')
    sta_if.active(True)
    sta_if.connect(wifi_ssid, wifi_password)
    while not sta_if.isconnected():
        pass
print("wifi OK")


def clearSDCard():
    # limpar dados do cartão SD caso necessario
    files = os.listdir("/sd")
    for file in files:
        try:
            os.remove(f"/sd/{file}")
        except:
            # arquivos obrigatórios
            pass


def GPS():
    # retorna os dados do gps
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
    if gpsdata['latitude'][1] == 'S':
        gpsdata['latitude'] = -gpsdata['latitude'][0]
    if gpsdata['longitude'][1] == 'W':
        gpsdata['longitude'] = -gpsdata['longitude'][0]
    if 'error' in gpsdata:
        del gpsdata['error']
    return gpsdata


def addMapPosition(name, latitude, longitude, session, info, icon):
    # adiciona a localizacao do satelite no mapa com base nos dados retornados pelo gps
    params = {
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
    response = urequests.get(url+params_str)


def batteryLevel():
    # retorna o nivel da bateria em porcentagem
    adc35 = ADC(Pin(35))
    adc35.atten(ADC.ATTN_11DB)
    adc35.width(ADC.WIDTH_12BIT)
    battery_level = adc35.read()
    return round((battery_level/2600)*100, 2)


def Temperature():
    # retorna a temperatura em graus celsius
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    i2c.writeto(0x40, b'\xf3')
    time.sleep_ms(70)
    t = i2c.readfrom(0x40, 2)
    temperature_ = -46.86+175.72*(t[0]*256+t[1])/65535
    return round(temperature_, 2)


def Pressure():
    # retorna a pressao em Pascal
    bus = SoftI2C(scl=Pin(22), sda=Pin(21))
    bmp280 = BMP280(bus)
    bmp280.use_case(BMP280_CASE_WEATHER)
    bmp280.oversample(BMP280_OS_HIGH)
    bmp280.normal_measure()
    pressure = bmp280.pressure
    return pressure


def Gyro():
    # retorna a taxa de giro nos eixos X, Y e Z
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    gyro_xyz = tuple(mpu9250s.gyro)

    return gyro_xyz


def Acceleration():
    # retorna a  taxa de aceleracao nos eixos X, Y e Z
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    acceleration_xyz = tuple(mpu9250s.acceleration)

    return acceleration_xyz


def CO2():
    # retorna o nível de CO2 em partes por milhao (ppm)
    bus = SoftI2C(scl=Pin(22), sda=Pin(21))
    sCCS811 = CCS811.CCS811(i2c=bus, addr=0x5A)
    ok = sCCS811.data_ready()
    return sCCS811.eCO2


def Humidity():
    # retorna a umidade em porcentagem
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    i2c.writeto(0x40, b'\xf5')
    time.sleep_ms(70)
    t = i2c.readfrom(0x40, 2)
    return -6+125*(t[0]*256+t[1])/65535


def Luminosity():
    # retorna a luminosidade em porcentagem
    adc34 = ADC(Pin(34))
    adc34.atten(ADC.ATTN_11DB)
    adc34.width(ADC.WIDTH_12BIT)
    light = adc34.read()  # max: 4095
    return round(light, 2)


def Magnetic():
    # retorna o campo magnetico em micro Tesla
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    magnetism_xyz = tuple(mpu9250s.magnetic)

    return magnetism_xyz


def getData(payload={}):
    ''' 
    retorna os dados dos sensores juntamente com
    o payload passado no parametro da funcao
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

def digitalWrite(pin, value):
  if value >= 1:
    Pin(pin, Pin.OUT).on()
  else:
    Pin(pin, Pin.OUT).off()

def takePhoto(pin=14):
    digitalWrite(pin, 1)
    digitalWrite(pin, 0) # manda o sinal para reiniciar a placa e tirar a foto
    time.sleep(500/1000) # espera 500 milissegundos
    digitalWrite(pin, 1)

def playSound(freq=1, duty=512, time_on=5):
    pwm25 = PWM(Pin(25), freq=(freq),  duty=duty)
    time.sleep(time_on)
    pwm25.deinit()

def soundOK(time_on=0.1):
    playSound(1, 512, time_on)

def debug():
    # apenas para na linha da funcao para fins de testes
    while(True):
        time.sleep(5)