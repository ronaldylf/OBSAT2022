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
from datetime import datetime, timedelta

current_path = os.path.join(os.path.dirname(__file__))
static_path = os.path.join(current_path, "static")
photos_path = os.path.join(current_path, "static", "fotos")
payloads_path = os.path.join(current_path, "static", "payloads")
paths = [
    static_path,
    photos_path,
    payloads_path
]
for path in paths:
    if not os.path.isdir(path):
        print(f"not exist, creating {path}")
        os.mkdir(path)

def now():
    utc_now = datetime.utcnow()
    br_now = utc_now-timedelta(hours=3)
    return br_now

def save_img(img):
    save_datetime = now()
    count = len(os.listdir(photos_path))+1

    filename = save_datetime.strftime(f"img_{count}__%d-%m-%Y__%H_%M_%S")+".jpg"
    path_and_file = os.path.join("static", "fotos", filename)
    print(f"path_and_file: {path_and_file}")
    cv2.imwrite(path_and_file, img)
    print("Image Saved: " + filename)


app = Flask(__name__, static_url_path="/static", static_folder=static_path)


@app.route('/', methods=['GET'])
def home():
    return render_template("index.html")


@app.route('/payloads')
def showPayloads():
    payload_filenames = os.listdir(payloads_path)
    payload_filenames = sorted(payload_filenames) # to order
    amount_payloads = len(payload_filenames)

    return render_template("showPayloads.html",
                           amount_executions=amount_payloads,
                           filenames=payload_filenames
                           )

@app.route('/fotos')
def showPhotos():
    photo_filenames = os.listdir(photos_path)
    photo_filenames = sorted(photo_filenames) # to order
    amount_photos = len(photo_filenames)
    return render_template("showPhotos.html",
                           amount_executions=amount_photos,
                           filenames=photo_filenames
                           )

@app.route('/payloads/<payload_name>')
def currentPayload(payload_name):
    with open(f"static/payloads/{payload_name}") as file:
        return json.loads(json.dumps(json.loads(str(file.read())), indent=4, sort_keys=False))



@app.route('/sendData', methods=['POST'])
def sendData():
    sent_datetime = now()
    print("DATA received in: " + now().strftime("%d/%m/%Y %H:%M:%S"))
    received_data = request.get_json()
    try:
        current_id = received_data['payload']['ciclo']
    except:
        current_id = 999
        print(f"did not found current_id, turning it to: {current_id}")

    data_name = sent_datetime.strftime(f"payload_{current_id}__%d-%m-%Y__%H_%M_%S")+".json"
    data_file = open(os.path.join(payloads_path, data_name), "w+")
    data_file.write(json.dumps(received_data, indent=4, sort_keys=False))
    data_file.close()

    return 'sent successful'


@app.route('/receivePhoto', methods=['POST'])
def receivingPhoto():
    print("PHOTO received: " + now().strftime("%d/%m/%Y %H:%M:%S"))
    received = request
    img = None
    if received.files:
        #print(received.files['imageFile'])
        # convert string of image data to uint8
        file = received.files['imageFile']
        #nparr = np.fromstring(file.read(), np.uint8) #old and deprecated
        nparr = np.frombuffer(file.read(), np.uint8)
        # decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        #h, w, _ = img.shape = img.shape
        #cv2.putText(img, "Hello World!!!", (x*0.7, y*0.7), cv2.FONT_HERSHEY_SIMPLEX, 2, 255)
        save_img(img)

        return "[SUCCESS] Image Received", 201

    print("something went wrong :(")
    return "something went wrong, but ok", 201

@app.route('/deletePayload/<filename>', methods=['DELETE'])
def deletePayload(filename):
    try:
        os.remove(os.path.join(payloads_path, filename))
    except:
        return "file may not exist", 500
    return 'payload deleted successful'

@app.route('/deletePhoto/<filename>', methods=['DELETE'])
def deletePhoto(filename):
    try:
        os.remove(os.path.join(photos_path, filename))
    except:
        return "file may not exist", 500
    return 'photo delete successful'


if __name__ == "__main__":
    server_port = 33
    app.run(host='0.0.0.0', port=server_port, debug=True)
