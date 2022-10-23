import cv2
import numpy as np
import utils.config as config
import tensorflow.keras as keras
import glob
from utils import config
import os

path = config.DATA_LOCATION + "cam_01_*.jpg"
f_list = glob.glob(path, recursive=True)

print (f_list[0])

# load model
model = keras.models.load_model(config.MODEL_FILE)

# load the test pictures
for f in f_list:
    img = cv2.imread(f)

    # prepare for inference
    snimg = cv2.resize(img.copy(), dsize=config.NET_SHAPE)
    nimg = np.array([snimg/255.0])
    mret = model.predict(nimg,batch_size=1)

    sout = np.array(mret[0]*255).astype(np.uint8)

    sout = cv2.cvtColor(sout,cv2.COLOR_BGR2RGB)
    img_over = cv2.addWeighted(snimg,1,sout,0.5, 1)

    img_over = cv2.resize(img_over, dsize=config.NET_SHAPE)
    cv2.imshow('test_segmentation', img_over)

    k = cv2.waitKey(0)

    if k== 27:
        os._exit(1)