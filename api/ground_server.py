from flask import (
    Flask,
    request,
    render_template,
)
import base64
from os import walk
import json

app = Flask(__name__)
server_port = 33

payload_filenames = next(walk("./static/payloads"), (None, None, []))[2]
amount_payload = len(payload_filenames)

photo_filenames = next(walk("./static/fotos"), (None, None, []))[2]
amount_photos = len(photo_filenames)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/payloads')
def showPayloads():
    return render_template("showPayloads.html",
    amount_executions=amount_payload,
    filenames=payload_filenames
    )

@app.route('/payloads/<payload_name>')
def currentPayload(payload_name):
    with open(f"static/payloads/{payload_name}") as file:
        return json.loads(json.dumps(json.loads(str(file.read())), indent=4, sort_keys=False))


@app.route('/fotos')
def showPhotos():
    return render_template("showPhotos.html",
    amount_executions=amount_photos,
    filenames=photo_filenames
    )

# @app.route('/fotos/<photo_name>')
# def currentPhoto(photo_name):
#     return render_template("currentPhoto.html", img_name=photo_name)

# server part (receive image and save)
@app.route('/sendData', methods=['POST'])
def sendImage():
    received_data = request.form.to_dict(flat=False)
    bytes_img = base64.decodebytes(received_data['payload']['foto'].encode("utf-8"))
    # saves received image
    execucao_atual = received_data['payload']['execucao_atual']
    image_name = f"fotos/foto{execucao_atual}.jpg"
    image_file = open(image_name, "wb")
    image_file.write(bytes_img)
    image_file.close()
    del received_data['foto']

    data_name = f"payload{execucao_atual}.json"
    data_file = open("payloads/"+data_name+".json", "w+")
    data_file.write(json.dumps(received_data, indent=4, sort_keys=False))
    data_file.close()
    

    return 'ok'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=server_port, debug=True)