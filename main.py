# importação dos módulos para processamento e manipulação dos dados
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

# variáveis editáveis
url_icon = "https://obsat.org.br/inscricoes/n2.png",  # url do ícone
team_id = 41  # id da equipe
session_id = 1111  # id de sessão
wifi_ssid = 'OBSAT_WIFI'  # nome da rede wifi
wifi_password = 'OBSatZenith1000'  # senha da rede wifi
# endereço na qual serão enviadas as requisições com os dados
payload_address = "http://192.168.0.1/"

# quantos minutos para cada execução (a cada 4 minutos uma execução)
allowed_delta = 4

# configuração gps
uartGPS = UART(2, tx=17, rx=16)
uartGPS.init(38400, bits=8, parity=None, stop=1)
gps = MicropyGPS()
gps.coord_format = 'dms'

# configuração microSD
os.mount(SDCard(), '/sd')

# configuração camera
camera.init(1)

# conexão com a rede wifi
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.scan()
sta_if.connect(wifi_ssid, wifi_password)


def getGPSData():
    # função que retorna os dados do gps
    if uartGPS.any():
        c = int.from_bytes(uartGPS.read(1), "big")
        stat = gps.update(chr(c))
        return {
            "latitude": gps.latitude,
            "longitude": gps.longitude,
            "altitude": gps.altitude,
            "velocidade": gps.speed,
        }

    return {"error": None}


def addMapPosition(name, latitude, longitude, session, info, icon):
    response = urequests.get(f"https://bipes.net.br/map/addMarker.php", params={
        'name': name,  # CubeSatPoincaré
        'lat': latitude,
        'long': longitude,
        'session': session,
        'info': info,
        'icon': icon,
    })


def takePhoto(filename=None):
    '''
    função retorna uma foto e armazena no
    cartão SD caso seja passado o nome do arquivo
    no parâmetro 'filename'
    '''
    photo = camera.capture()  # tira a foto
    if (type(filename) == str):
        file = open(filename+".jpg", "bw")
        file.write(photo)
        file.close()
    return photo


def batteryLevel():
    # função que retorna o nível da bateria
    adc35 = ADC(Pin(35))
    adc35.atten(ADC.ATTN_11DB)
    adc35.width(ADC.WIDTH_12BIT)
    battery_level = adc35.read()
    return battery_level


def currentTemperature():
    # função que retorna a atual temperatura
    i2c = I2C(scl=Pin(22), sda=Pin(21))
    i2c.writeto(0x40, b'\xf3')
    time.sleep_ms(70)
    t = i2c.readfrom(0x40, 2)
    temperature = -46.86+175.72*(t[0]*256+t[1])/65535
    return temperature


def currentPressure():
    # função que retorna a atual pressão
    bus = I2C(scl=Pin(22), sda=Pin(21))
    bmp280 = BMP280(bus)
    bmp280.use_case(BMP280_CASE_WEATHER)
    bmp280.oversample(BMP280_OS_HIGH)
    bmp280.normal_measure()
    pressure = bmp180.temperature
    return pressure


def currentGyro():
    # função que retorna a atual taxa de giro nos eixos X, Y e Z
    i2c = I2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    gyro_xyz = mpu9250s.gyro
    return list(gyro_xyz)


def currentAcceleration():
    # função que retorna a atual taxa de aceleração nos eixos X, Y e Z
    i2c = I2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(i2c)
    acceleration_xyz = mpu9250s.acceleration
    return list(acceleration_xyz)


def now():
    '''
    função que retorna um objeto com a data e hora (datetime) 
    no fuso horário do estado do Maranhão
    '''

    return (datetime.utcnow()-timedelta(hours=3))


def getData(payload={}):
    ''' 
    função que retorna os dados dos sensores juntamente com
    o payload passado no parâmetro da função.
    '''
    data = {
        "equipe": team_id,  # id da equipe
        "bateria": batteryLevel(),
        "temperatura": currentTemperature(),
        "pressao": currentPressure(),
        "giroscopio": currentGyro(),
        "acelerometro": currentAcceleration(),
        "payload": payload
    }
    return data


execution_current = 0  # quantidade de execuções atual
start_moment = now()  # objeto do momento de início da missão
while (True):
    t0 = now()
    t = now()
    while ((t-t0) < timedelta(minutes=allowed_delta)):
        t = now()
        # loop contínuo enquanto espera a próxima execução

    execution_current += 1  # adiciona 1 a quantidade de execuções
    current_photo = takePhoto(f"foto{execution_current}")  # foto tirada
    ######### falta mandar a foto para visualização em baixo #########
    # objeto dos dados juntamente com o payload
    general_data = getData({
        "execucao_atual": execution_current,
        # data formatada em DD/MM/AAAA H:M:S
        "momento": now().strftime("%d/%m/%Y %H:%M:%S"),
        "gps": getGPSData(),
    })
    # transforma os dados para uma string em formato JSON
    json_data = json.dumps(general_data)

    addMapPosition(
        f"CubeSatPoincaré({execution_current})",  # título, sendo
        general_data['gps']['latitude'],  # latitude
        general_data['gps']['longitude'],  # longitude
        session_id,  # id de sessão
        json_data,  # informações dos sensores e do payload
        url_icon  # url do ícone
    )

    # envia a requisição HTTP pelo método POST para a sonda Zenith
    response = urequests.post(url=payload_address, json=json_data)


end_moment = now()  # objeto do momento do fim da missão
print("end of mission")
