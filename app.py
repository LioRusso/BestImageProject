from __future__ import division
from flask import Flask, request, json
from pip._vendor import requests
from PIL import Image

ENDPOINT = "https://westcentralus.api.cognitive.microsoft.com/face/v1.0"
SUBSCRIPTION_KEY1 = "711a09d7020444fabd364139afdfc121"
SUBSCRIPTION_KEY2 = "ce64da0efb0e4758a3fdbeffdc1d25a5"

app = Flask(__name__)


def compare_best_image(best, res, image_file):
    try:
        im = Image.open(image_file)
        width, height = im.size
        image_size = width * height
    except IOError:
        return best

    if res is None:
        return best

    if best is None:
        return {'file_name': image_file, 'image_size': image_size, 'metadata': res}

    image_face_size = res['faceRectangle']['width'] * res['faceRectangle']['height']
    best_size = best['image_size']
    best_result = best['metadata']
    best_face_size = best_result['faceRectangle']['width'] * best_result['faceRectangle']['height']

    if best_face_size / best_size < image_face_size / image_size:
        return {'file_name': image_file, 'image_size': image_size, 'metadata': res}

    return best


def read_image(image_file):
    try:
        with open(image_file, "rb") as image:
            image_content = image.read()
            image_bytes = bytearray(image_content)
        return image_bytes
    except (OSError, IOError):
        return None


def get_face_data(image_bytes):
    face_api_url = ENDPOINT + '/detect'
    headers = {'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY1, 'Content-Type': 'application/octet-stream'}

    params = {
        'returnFaceId': 'true',
        'returnFaceLandmarks': 'false',
        'returnFaceAttributes': 'age,gender,headPose,smile,facialHair,glasses,emotion,hair,makeup,occlusion,accessories,blur,exposure,noise'
              }

    try:
        response = requests.post(face_api_url, params=params, headers=headers, data=image_bytes, timeout=10)
    except requests.Timeout:
        raise ValueError('Call to Azure Failed due to Timeout')
    except requests.ConnectionError:
        raise ValueError('Call to Azure Failed due to Connection Error')

    res_json = response.json()
    # TODO: specific status_codes handling.
    if response.status_code != 200:
        raise ValueError(res_json['error']['message'])

    return res_json


@app.route('/best_image', methods=['POST'])
def best_image():
    images_files = request.get_json()

    if len(images_files) == 0:
        return "Mo images were received, Please supply a list of images in json format."

    best_image_result = None
    for image_file in images_files:
        #  1. read the image bytes from the filename.
        image_bytes = read_image(image_file)
        if image_bytes is None:
            return "Failed to open/read " + image_file + ", Please make sure file exists."

        #  2. send the image to azure.
        try:
            res = get_face_data(image_bytes)
        except ValueError as err:
            return 'Failed to get image metadata for image' + image_file + ', received Error:' + err.args[0]

        #  3. compare response to see who is best image
        #     compare the image size with the face size.
        if len(res) != 0:
            best_image_result = compare_best_image(best_image_result, res[0], image_file)

    if best_image_result is None:
        return 'Failed to calculate Best Image, please try again'

    best_image_result.pop('image_size', None)
    app_json = json.dumps(best_image_result)
    return app_json

if __name__ == '__main__':
    app.run()
