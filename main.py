# importao dos mdulos para processamento e manipulao dos dados
import network
from machine import (
    Pin,
    SoftI2C,
    UART,
    ADC,
    SDCard
)
import urequests
#import camera
import os
from mini_micropyGPS import MicropyGPS
from bmp280 import *
from mpu9250 import MPU9250
import rtttl, songs
import json
import time
import base64
import sys

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
wifi_ssid = 'MAKE_CURSINHO'  # nome da rede wifi
wifi_password = 'nossainternet'  # senha da rede wifi
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


def currentTemperature():
    # funo que retorna a atual temperatura
    SoftI2C = SoftI2C(scl=Pin(22), sda=Pin(21))
    SoftI2C.writeto(0x40, b'\xf3')
    time.sleep_ms(70)
    t = SoftI2C.readfrom(0x40, 2)
    temperature = -46.86+175.72*(t[0]*256+t[1])/65535
    return temperature


def currentPressure():
    # funo que retorna a atual presso
    bus = SoftI2C(scl=Pin(22), sda=Pin(21))
    bmp280 = BMP280(bus)
    bmp280.use_case(BMP280_CASE_WEATHER)
    bmp280.oversample(BMP280_OS_HIGH)
    bmp280.normal_measure()
    pressure = bmp280.pressure
    return pressure


def currentGyro():
    # funo que retorna a atual taxa de giro nos eixos X, Y e Z
    SoftI2C = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(SoftI2C)
    gyro_xyz = list(mpu9250s.gyro)
    return {
        'x': gyro_xyz[0],
        'y': gyro_xyz[1],
        'z': gyro_xyz[2]
    }


def currentAcceleration():
    # funo que retorna a atual taxa de acelerao nos eixos X, Y e Z
    SoftI2C = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu9250s = MPU9250(SoftI2C)
    acceleration_xyz = mpu9250s.acceleration
    return list(acceleration_xyz)


def now(return_seconds=False):
    '''
    funo que retorna um objeto com os dados temporais
    no fuso horário do estado do Maranhão (UTC-3)
    '''

    tseconds = time.time()-(3*60*60)
    if return_seconds: return tseconds

    return (time.gmtime(tseconds))


def getData(payload={}):
    ''' 
    funo que retorna os dados dos sensores juntamente com
    o payload passado no parmetro da funo.
    '''
    data = {
        "equipe": team_id,  # id da equipe
        "bateria": batteryLevel(),
        "temperatura": currentTemperature(), # ok
        "pressao": currentPressure(),
        "giroscopio": currentGyro(),
        "acelerometro": currentAcceleration(),
        "payload": payload
    }
    return data

print("starting...")
execution_current = 0  # número da execução atual
start_moment = now()  # objeto do momento de incio da misso
##########################
# teste para checagem dos dados
#play = rtttl.play(Pin((25), Pin.OUT), songs.find('Super Mario - Main Theme'))
#print("end song")

while(True):
    # data = {
    #     "equipe": team_id,  # id da equipe
    #     "bateria": batteryLevel(), # ok
    #     "temperatura": currentTemperature(), # ok
    #     "pressao": currentPressure(), # ok
    #     "giroscopio": currentGyro(),
    #     "acelerometro": currentAcceleration(),
    #     "payload": payload
    # }
    print(f"pressão: {currentGyro()}")
    time.sleep(1)
##########################
while (True):
    t0 = now(return_seconds=True)
    delta_seconds = 0
    while (delta_seconds < (max_delta*60)):
        t = now(return_seconds=True)
        delta_seconds = t - t0
        # loop contínuo enquanto espera a próxima execução
        percentage_complete = round((delta_seconds/(max_delta*60))*100, 2)
        print(f"{delta_seconds}/{(max_delta*60)} ({max_delta} minutos) -> {percentage_complete}%")
        time.sleep(1)

    print("\n")
    print("iniciando rotina")
    execution_current += 1  # adiciona 1 a quantidade de execuções
    moment_current = now()
    gps_data = getGPSData()

    photo_name = f"foto{execution_current}"
    bytes_photo = takePhoto(photo_name)  # foto tirada

    # objeto dos dados juntamente com o payload
    general_data = getData({
        "execucao_atual": execution_current,
        #"momento": time.strftime("%d/%m/%Y %H:%M:%S", moment_current), # data formatada em dd/MM/AAAA H:M:S
        "momento": time.localtime(gps_data['timestamp']),
        "gps": gps_data,
    })


    # checar se o payload está com no máximo 90 bytes: sys.getsizeof(general_data['payload'])

    # transforma os dados para uma string em formato JSON
    json_data = json.dumps(general_data)

    # armazenamento dos dados atuais
    data_name = f"payload{execution_current}"
    data_file = open("payloads/"+data_name+".json", "w+")
    data_file.write(json_data)
    data_file.close()

    # posiciona um cone no mapa com base nos dados do sensor gps
    addMapPosition(
        f"CubeSatPoincaré({execution_current})",  # título, sendo
        general_data['gps']['latitude'],  # latitude
        general_data['gps']['longitude'],  # longitude
        session_id,  # id de sesso
        f"execucao nmero {execution_current}",  # número da execuo
        url_icon  # url do ícone
    )
    

    # envia a requisio HTTP pelo mtodo POST para a sonda Zenith
    response = urequests.post(url=payload_address, json=json_data)

    # cópia dos dados + adição da foto
    # b64_photo = base64.b64encode(bytes_photo)
    # general_data['payload']['foto'] = b64_photo.decode("utf-8")
    # json_data = json.dumps(general_data)
    # response = urequests.post(url=url_ground_server, json=json_data)


end_moment = now()  # objeto do momento do fim da missão
print("end of mission")