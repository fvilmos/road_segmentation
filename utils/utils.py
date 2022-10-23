'''
Author: fvilmos
https://github.com/fvilmos
'''

import numpy as np
import json
import cv2
import os 

def load_data(file_name,filter_fn=[lambda x:True], file_tag=['file']):
    f = open(file_name, "r")
    lines = f.readlines()
    data = []
    
    tmp = str.split(file_name,"\\")
    # reconstruct file path
    dir_name =''
    for p in range(len(tmp)-1):
        dir_name +=tmp[p] + '\\'

    # read line by line, de-serialize to dict
    for l in lines:
        obj_dict = json.loads(l)
        
        # test if img exist
        for ft in file_tag:
            test_img_path = os.path.exists(dir_name + obj_dict[ft])
            if test_img_path == True:

                #filter the data
                test_ret = []
                for fn in filter_fn:
                    if fn(obj_dict) == True:
                        test_ret.append(True)

                if len(test_ret)>0:
                    file = obj_dict[ft]
                    obj_dict[ft] = dir_name+file
                    #print (obj_dict)
                    data.append(obj_dict)        
        
    f.close()
    return np.array(data)

def normalization(data):
    # scale values for a specific domain
    # y = (x-xmin)/(xmax-xmin) => [0..1]
    xmin = np.min(data)
    xmax = np.max(data)
    
    return (data-xmin)/(xmax-xmin)

def fast_normalization(data):    
    return data/255.0

def standardizarion(data):
    # center data round standard deviation
    # y = (x-mean)/std
    xmean = np.mean(data)
    xstd = np.std(data)
    return (data-xmean)/xstd


def puttext_bg(img,text='',position=(10,160), font_type=None, font_size=0.4, font_color=[0,255,0],bg_color=[0,0,0],font_thickness=1):
    '''
    create a text on the image with a background color
    '''
    if font_type is None:
        font_type = cv2.FONT_HERSHEY_SIMPLEX
    (t_w,t_h),_ = cv2.getTextSize(text, font_type, font_size, font_thickness)
    cv2.rectangle(img, position, (position[0] + t_w, position[1] + t_h), bg_color, -1)
    cv2.putText(img,text ,(position[0], int(position[1]+t_h+font_size-1)),font_type,font_size,[0,255,0],font_thickness)