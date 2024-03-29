try:
    # variaveis, funcoes e setup dos componentes
    exec(open('./main_functions.py').read(), globals())
    # toca uma nota musical bem rapido para indicar sucesso no arranque inicial
    soundOK(500/1000)
    import os
    os.chdir('/')
except Exception as e:
    # toca uma nota musical por mais tempo para indicar erro em alguma parte do programa de configuracao e encerra
    print("ERROR: " + str(e))
    import sys
    import time
    from machine import Pin, PWM
    pwm25 = PWM(Pin(25), freq=(7040),  duty=512)
    time.sleep(1)
    pwm25.deinit()
    raise e

cycle_current = 0  # variavel para contagem do numero de execucoes a cada 4 minutos

while (True):
    t0 = time.time()
    delta_seconds = 0
    # loop continuo enquanto espera a proxima execucao
    print("aguardando proximo ciclo...")
    while (delta_seconds < (max_delta*60)):
        time.sleep(60)
        t = time.time()
        delta_seconds = t - t0
        percentage_complete = round((delta_seconds/(max_delta*60))*100, 2)
        print(f"({round(delta_seconds/60, 2)} minutos) {delta_seconds}/{(max_delta*60)} ({max_delta} minutos) -> {percentage_complete}%")

    print("\n")
    print("iniciando rotina")
    now_str = "erro"
    try:
        now_obj = getNowObject()
        now_str = time.strftime("%d-%m-%Y__%H_%M_%S", now_obj)
        print("data atual capturada com sucesso!")
    except:
        print("nao foi possivel capturar a data atual, prosseguindo...")
    cycle_current += 1  # adiciona 1 a quantidade de execucoes
    gps_data = GPS()

    print("tirando foto...")
    takePhoto()
    soundOK(500/1000)

    print("coletando dados dos sensores...")
    general_data = requiredData()  # dict dos dados obrigatorios
    general_data['payload'] = {  # adiciona o payload para as informações que serão enviadas
        "umidade": getHumidity(),
        "co2": getCarbon(),
        "ciclo": cycle_current,
        "datatempo": now_str
    }

    print("dados coletados:")
    # printa os dados de cima pra baixo
    for key in general_data:
        print((key, general_data[key]))

    # armazenamento dos dados atuais
    print("armazenando os dados no cartao SD...")
    try:
        data_file = open(f"/sd/payload{cycle_current}.json", "w+")
        data_file.write(json.dumps(general_data))
        data_file.close()
        print("dados armazenados")
    except Exception as e:
        print(f"algo deu errado com o armazenamento dos dados no cartao: {str(e)}")

    # posiciona um icone no mapa com base nos dados do sensor gps
    try:
        addMapPosition(
            f"CubeSatPoincare({cycle_current})",  # título
            gps_data['latitude'],  # latitude
            gps_data['longitude'],  # longitude
            session_id,  # id de sessao
            str(gps_data),  # dados do gps
            url_icon  # url do icone
        )
        print("localizacao definida no mapa")
    except:
        print("algo de errado ocorreu ao tentar se posicionar no mapa, prosseguindo...")

    # envia a requisicao HTTP pelo metodo POST para a sonda Zenith e para outros enderecos
    print(f"enviando para {len(payload_addresses)} servidores remotos...")
    for address in payload_addresses:
        try:
            response = urequests.post(url=address, json=general_data)
            print(f"enviado para {address}")
        except Exception as e:
            print(str(e))
            print(f"dados nao enviados, problema em {address}")

    print(f"terminado ciclo {cycle_current}")

print("end of mission")
