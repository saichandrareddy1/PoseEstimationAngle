import os
import sys
import argparse
import cv2
import time
import warnings
import pandas as pd
import numpy as np
from graph import plot
from CSV_save import csv_create
warnings.filterwarnings('ignore')

from config_reader import config_reader

from processing import extract_parts, draw, plotting
from angle_preprocess import extract_parts_angle, draw_angle

from model.cmu_model import get_testing_model
from Convertor.convert_video import convert_video
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

currentDT = time.localtime()
start_datetime = time.strftime("-%m-%d-%H-%M-%S", currentDT)



def video_cap():    
    path_model_h5 = 'model.h5'
    keras_weights_file = path_model_h5
    #Analysis for the every n frames
    frame_rate_ratio = 1
    
    #Int 1 (fastest, lowest quality) to 4 (slowest, highest quality)
    process_speed = 1
    #ending_frame = args.end
    print('start processing...')

    # Video input
    video_file = '/home/saireddy/SaiReddy/Desk/Flask/OrbitPose/videos/sit.mp4'
    print(video_file)
    
    # Output location
    video_output = '/home/saireddy/SaiReddy/Desk/Flask/OrbitPose/videos/output/sit.avi'

    model = get_testing_model()
    model.load_weights(keras_weights_file)

    # load config
    params, model_params = config_reader()

    # Video reader
    #cam = cv2.VideoCapture(video_file)
    cam = cv2.VideoCapture(video_file)
    
    input_fps = cam.get(cv2.CAP_PROP_FPS)
    print("input frames per second:-", input_fps)

    ret_val, orig_image = cam.read()

    video_length = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
    print("total frames in a video:-", video_length)

    # Video writer
    output_fps = input_fps / frame_rate_ratio
    print("out put frames:-", output_fps)
    
    frame_width = int(cam.get(3))
    frame_height = int(cam.get(4))

    print("width:-", frame_width)
    print("Height:-", frame_height)
    
    out = cv2.VideoWriter(video_output, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),output_fps, (frame_width, frame_height))

    #out = cv2.VideoWriter(video_output, cv2.VideoWriter_fourcc(*'DIVX'),output_fps, (frame_width, frame_height))
    
    scale_search = [1, .5, 1.5, 2]  # [.5, 1, 1.5, 2]
    scale_search = scale_search[0:process_speed]

    params['scale_search'] = scale_search

    i = 0  # default is 0
    while(cam.isOpened()) and ret_val is True:

        if ret_val is None:
            break
        
        if i % frame_rate_ratio == 0:
            input_image = cv2.cvtColor(orig_image, cv2.COLOR_RGB2BGR)
            tic = time.time()
            all_peaks1, subset1, candidate1 = extract_parts_angle(input_image, params, model, model_params)
            canvas, theta5, theta6, Angle5, Angle6 = draw_angle(orig_image, all_peaks1, subset1, candidate1)
            cv2.rectangle(canvas, (645, 0), (900, 35), color=(0, 255, 0), thickness=2)
            cv2.putText(canvas, "Left  :- {0:.2f}".format(float(theta5)), (650, 15), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 225))
            cv2.putText(canvas, "Right :- {0:.2f}".format(float(theta6)), (650, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255))
            print('Processing frame: ', i)
            toc = time.time()
            print(Angle5)
            print(Angle6)
            out.write(canvas)
        ret_val, orig_image = cam.read()
        i += 1
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
    
    return Angle5, Angle6

Angle5, Angle6 = video_cap()
##csv_create(_, _, Angle5, Angle6)
##plot(_, _, Angle5, Angle6)
    


