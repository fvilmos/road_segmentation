'''
Author: fvilmos
https://github.com/fvilmos
'''

# use GPU for training
USE_GPU = 1

# image strored
IMG_W,IMG_H = (160,120)
NET_SHAPE=(160,20)
IMG_CHANNELS = 3

# trained model
MODEL_FILE = '.\\seg.h5'

# training /test database releated info
DATA_LOCATION='.\\data\\**\\'
FILE = "*info.rec"

