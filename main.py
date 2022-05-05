try:
    # variaveis, funcoes e setup dos componentes
    exec(open('./main_functions.py').read(), globals())
    # toca uma nota musical bem rápido para indicar sucesso no arranque inicial
    from machine import PWM, Pin
    import time
    import os
    pwm25 = PWM(Pin(25), freq=(1),  duty=512)
    time.sleep(0.1)
    pwm25.deinit()
    os.chdir('/')
except Exception as e:
    # toca uma nota musical por mais tempopara indicar erro em alguma parte do programa de configuracao e encerra
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
    cycle_current += 1  # adiciona 1 a quantidade de execucoes
    gps_data = GPS()

    print("coletando dados dos sensores...")
    # objeto dos dados juntamente com o payload
    general_data = getData({
        "umidade": Humidity(),
        "co2": CO2(),
        "datetime": "%d/%d/%d %d:%d:%d" % gps_data['datetime']
    })
    print("dados coletados:")
    # printa os dados de cima pra baixo
    for key in general_data:
        print((key, general_data[key]))

    # transforma os dados para uma string em formato JSON
    json_data = json.dumps(general_data)

    # armazenamento dos dados atuais
    print("armazenando os dados no cartão SD...")
    data_file = open(f"/sd/payload{cycle_current}.json", "w+")
    data_file.write(json.dumps(general_data))
    data_file.close()
    print("dados armazenados")

    # posiciona um icone no mapa com base nos dados do sensor gps
    addMapPosition(
        f"CubeSatPoincare({cycle_current})",  # título
        gps_data['latitude'],  # latitude
        gps_data['longitude'],  # longitude
        session_id,  # id de sessao
        str(gps_data),  # dados do gps
        url_icon  # url do icone
    )
    print("localização definida no mapa")

    # envia a requisicao HTTP pelo metodo POST para a sonda Zenith e para outros endereços
    print(f"enviando para {len(payload_addresses)} servidores remotos...")
    for address_current in payload_addresses:
        response = urequests.post(url=address_current, json=json_data)
        print(f"enviado para {address_current}")

    print(f"terminado ciclo {cycle_current}")

print("end of mission")
