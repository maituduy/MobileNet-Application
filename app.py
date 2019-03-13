from __future__ import division, print_function
# coding=utf-8
import sys
import os
import glob
import re
import numpy as np
import json

# Flask utils
from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer

# Define a flask app
app = Flask(__name__)
from mxnet.gluon.model_zoo.vision import mobilenet1_0

MODEL_PATH = 'models/MobileNetV1_3.params'
names = ['conservative','dressy','ethnic','fairy','feminine','gal','girlish','kireime-casual','lolita',
         'mode','natural','retro','rock','street']
# Load your trained model
net = mobilenet1_0(classes=14)
net.load_parameters(MODEL_PATH )
# print('Model loaded. Start serving...')

from mxnet import nd, gluon, image
def getTop(data,net,names,k=1):
    data = image.imresize(data,256,256)
    data = image.center_crop(data,(224,224))
    data = nd.transpose(data[0],(2,0,1))/255
    data = nd.expand_dims(data,0)
    result = nd.softmax(net(data))[0]    
    probs = result.sort()[-k:]
    result = result.argsort()[-k:]
    temp = []
    for i in result:
        temp.append(names[int(i.asscalar())])
    json = {}
    for x,y in zip(temp,probs):
        json[x] = str(y.asscalar()*100)
    return json

@app.route('/', methods=['GET'])
def index():
    # Main page
    return render_template('index.html')


@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['file']

        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)

        img = image.imread(file_path).astype('float32')
        result = getTop(img,net,names,5)
        return json.dumps(result)

    return None


if __name__ == '__main__':
    # app.run(port=5002, debug=True)

    # Serve the app with gevent
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()
