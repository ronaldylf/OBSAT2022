exec(open('./main_functions.py').read(),globals())
#from main_functions import *

execution_current = 0  # nmero da execuo atual
start_moment = now()  # objeto do momento de incio da misso

# teste para checagem dos dados
#play = rtttl.play(Pin((25), Pin.OUT), songs.find('Super Mario - Main Theme'))
#print("end song")

while(True):
    # data = {
    #     "equipe": team_id,  # id da equipe
    #     "bateria": batteryLevel(), # ok
    #     "temperatura": Temperature(), # ok
    #     "pressao": Pressure(), # ok
    #     "giroscopio": Gyro(), # ok
    #     "acelerometro": Acceleration(), # ok
    #     "payload": {
    #         "execucao_atual": execution_current,
    #         #"momento": time.strftime("%d/%m/%Y %H:%M:%S", moment_current), # data formatada em dd/MM/AAAA H:M:S
    #         "momento": time.localtime(gps_data['timestamp']),
    #         "gps": gps_data,
    #         "co2": CO2(),
    #         "umidade": Humidity(),
    #         "luminosidade": Luminosity(),
    #         "magnetometro": Magnetic()
    #    }
    # }
    print(f"magnetometro: {Magnetic()}")
    time.sleep(1)

while (True):
    t0 = now(return_seconds=True)
    delta_seconds = 0
    while (delta_seconds < (max_delta*60)):
        t = now(return_seconds=True)
        delta_seconds = t - t0
        # loop contnuo enquanto espera a prxima execuo
        percentage_complete = round((delta_seconds/(max_delta*60))*100, 2)
        print(f"{delta_seconds}/{(max_delta*60)} ({max_delta} minutos) -> {percentage_complete}%")
        time.sleep(1)

    print("\n")
    print("iniciando rotina")
    execution_current += 1  # adiciona 1 a quantidade de execues
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
        "co2": CO2(),
        "umidade": Humidity(),
        "luminosidade": Luminosity(),
        "magnetometro": Magnetic()
    })


    # checar se o payload est com no mximo 90 bytes: sys.getsizeof(general_data['payload'])

    # transforma os dados para uma string em formato JSON
    json_data = json.dumps(general_data)

    # armazenamento dos dados atuais
    data_name = f"payload{execution_current}"
    data_file = open("payloads/"+data_name+".json", "w+")
    data_file.write(json_data)
    data_file.close()

    # posiciona um cone no mapa com base nos dados do sensor gps
    addMapPosition(
        f"CubeSatPoincar({execution_current})",  # ttulo, sendo
        general_data['gps']['latitude'],  # latitude
        general_data['gps']['longitude'],  # longitude
        session_id,  # id de sesso
        f"execucao nmero {execution_current}",  # nmero da execuo
        url_icon  # url do cone
    )
    

    # envia a requisio HTTP pelo mtodo POST para a sonda Zenith
    response = urequests.post(url=payload_address, json=json_data)

    # cpia dos dados + adio da foto
    # b64_photo = base64.b64encode(bytes_photo)
    # general_data['payload']['foto'] = b64_photo.decode("utf-8")
    # json_data = json.dumps(general_data)
    # response = urequests.post(url=url_ground_server, json=json_data)


end_moment = now()  # objeto do momento do fim da misso
print("end of mission")