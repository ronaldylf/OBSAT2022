from flask import Flask, request
import base64

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def hello():
    resp_str = f'''
<h1>Hello world!</h1>
Seus dados:
IP: {request.remote_addr}
'''
    print(resp_str)
    return resp_str

# server part (receive image and save)
@app.route('/sendImage', methods=['POST'])
def sendImage():
    received_data = request.form.to_dict(flat=False)
    bytes_img = base64.decodebytes(received_data['payload']['foto'].encode("utf-8"))
    # saves received image
    execucao_atual = received_data['payload']['execucao_atual']
    image_name = f"photos/foto{execucao_atual}.jpg"
    image_file = open(image_name, "wb")
    image_file.write(bytes_img)
    image_file.close()

    return 'ok'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=server_port, debug=False)