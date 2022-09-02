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
import time
import sys
import _thread
import math

# variveis editveis
team_id = "01"  # id da equipe
session_id = 1111  # id de sessao para visualizacao do satelite no mapa
wifi_ssid = 'OBSAT_TESTES'  # nome da rede wifi (padrao: OBSAT_WIFI)
wifi_password = 'obsatsenha'  # senha da rede wifi (padrao: OBSatZenith1000)
# endereco na qual serao enviadas as requisicoes com os dados
earth_server = "http://192.168.60.201:33" # endereco terrestre (padrao: http://161.35.3.156:33)
payload_addresses = [
    "http://192.168.0.1/",  # sonda
    f"{earth_server}/sendData",
    "https://obsat.org.br/teste_post/envio.php",  # endereço de testes
]
# url do icone que aparecera no mapa
url_icon = "https://i.imgur.com/nHMQQ2Y.jpeg"
# quantos minutos para cada execucao (padrao: a cada 4 minutos uma execucao)
max_delta = 4

# configuracao gps
uartGPS = UART(2, tx=17, rx=13)
uartGPS.init(9600, bits=8, parity=None, stop=1)
gps = MicropyGPS(-3, "dd")  # utc-3 (fuso horario brasileiro)
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
def clearSDCard():
    # limpar dados do cartao SD caso necessario
    files = os.listdir("/sd")
    for file in files:
        try:
            os.remove(f"/sd/{file}")
        except:
            pass # arquivos obrigatorios

print("preparando cartao sd")
sd = sdcard.SDCard(SPI(2), Pin(15))
try:
    if 'sd' in os.listdir('/'): # se estiver montado, nao faz nada
        print("sdcard ja montado, que beleza!")
    else: # caso tenha sido removido e adicionado, monta
        print("montando cartao...")
        os.mount(sd, '/sd')
    print("SDCard OK")
except Exception as e:
    print(f"nao foi possível montar o SDCard: {str(e)}")


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


def getTemperature():
    # retorna a temperatura em graus celsius
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    i2c.writeto(0x40, b'\xf3')
    time.sleep_ms(70)
    t = i2c.readfrom(0x40, 2)
    temperature_ = -46.86+175.72*(t[0]*256+t[1])/65535
    return round(temperature_, 2)


def getPressure():
    # retorna a pressao em Pascal
    bus = SoftI2C(scl=Pin(22), sda=Pin(21))
    bmp280 = BMP280(bus)
    bmp280.use_case(BMP280_CASE_WEATHER)
    bmp280.oversample(BMP280_OS_HIGH)
    bmp280.normal_measure()
    pressure = bmp280.pressure
    return round(pressure, 2)


def getGyro():
    # retorna a taxa de giro nos eixos X, Y e Z em graus por segundo
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    gyro_xyz = []
    for axis in mpu9250s.gyro: gyro_xyz.append(round(axis, 2))
    
    return tuple(gyro_xyz)


def getCurrentAngles():
    # retorna a angulacao do satelite no eixos X, Y e Z em graus
    accelerations = list(getAcceleration())
    angles = []
    for axis in accelerations:
        if (axis / 9.8) > 1: axis = 1
        if (axis / 9.8) < -1: axis = -1
        angle_current = math.asin(axis / 9.8) / math.pi * 180
        angles.append(round(angle_current, 2))
    return tuple(angles)

def getAcceleration():
    # retorna a  taxa de aceleracao nos eixos X, Y e Z em m/s2
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    acceleration_xyz = []
    for axis in mpu9250s.acceleration: acceleration_xyz.append(round(axis, 2))
    return tuple(acceleration_xyz)


def getCarbon():
    # retorna o nível de CO2 em partes por milhao (ppm)
    bus = SoftI2C(scl=Pin(22), sda=Pin(21))
    sCCS811 = CCS811.CCS811(i2c=bus, addr=0x5A)
    ok = sCCS811.data_ready()
    return sCCS811.eCO2


def getHumidity():
    # retorna a umidade em porcentagem
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    i2c.writeto(0x40, b'\xf5')
    time.sleep_ms(70)
    t = i2c.readfrom(0x40, 2)
    calculo = (-6+125*(t[0]*256+t[1])/65535)
    return round(calculo, 2)


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


def requiredData():
    ''' 
    retorna os dados obrigatorios dos sensores
    '''
    data = {
        "equipe": team_id,  # id da equipe
        "bateria": batteryLevel(),
        "temperatura": getTemperature(),
        "pressao": getPressure(),
        "giroscopio": getGyro(),
        "acelerometro": getAcceleration(),
    }
    return data


def digitalWrite(pin, value):
    if value >= 1:
        Pin(pin, Pin.OUT).on()
    else:
        Pin(pin, Pin.OUT).off()


def takePhoto(pin=14):
    digitalWrite(pin, 1)
    digitalWrite(pin, 0)  # manda o sinal para reiniciar a placa e tirar a foto
    time.sleep(500/1000)  # espera 500 milissegundos
    digitalWrite(pin, 1)


def playSound(freq=1, duty=512, time_on=5):
    pwm25 = PWM(Pin(25), freq=(freq),  duty=duty)
    time.sleep(time_on)
    pwm25.deinit()


def soundOK(time_on=0.1):
    playSound(1, 512, time_on)

def getNowObject():
    url = f"{earth_server}/getNow"
    resp = urequests.get(url)
    obj = time.localtime(float(resp.text))
    return obj

def debug():
    # apenas para na linha da funcao para fins de testes
    while(True):
        time.sleep(5)