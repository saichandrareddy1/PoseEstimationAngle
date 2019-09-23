import os
import sys
import argparse
import cv2
import time
import warnings
import pandas as pd
warnings.filterwarnings('ignore', message='Done!')
from config_reader import config_reader

from processing import extract_parts, draw, plotting

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
    video_file = '/home/saireddy/Desktop/Flask/OrbitPose/videos/4.avi'
    
    # Output location
    video_output = '/home/saireddy/Desktop/Flask/OrbitPose/videos/output/pose8.avi'

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
            # generate image with body parts
            all_peaks, subset, candidate = extract_parts(input_image, params, model, model_params)


            #print("All peaks", all_peaks)
            #print("Dimentio 1", all_peaks[0])
            #print("All Substes", subset)
            #print("All candidate",candidate)
            
            canvas, theta, theta1, theta2, theta3, Angle1, Angle2, Angle3, Angle4 = draw(orig_image, all_peaks, subset, candidate)

            #chr(176)
            #label = "Right hand angle is :-()".format(theta)
            cv2.rectangle(canvas, (0, 0), (265, 35), color=(0, 255, 0), thickness=2)
            cv2.putText(canvas, "right Hand angle :- {0:.2f}".format(float(theta)), (30, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))
            cv2.putText(canvas, "right leg angle :- {0:.2f}".format(float(theta2)), (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))

            cv2.rectangle(canvas, (645, 0), (900, 35), color=(0, 255, 0), thickness=2)
            cv2.putText(canvas, "left Hand angle :- {0:.2f}".format(float(theta1)), (650, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 225))
            cv2.putText(canvas, "left leg angle :- {0:.2f}".format(float(theta3)), (650, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))
            
            #print("Theta in opencv ======", theta)
            #print("Theta1 in opencv ======", theta1)
            print("Theta2 in opencv ======", theta3)
            
            print('Processing frame: ', i)
            toc = time.time()
            #print('processing time is %.5f' % (toc - tic))

            out.write(canvas)

        ret_val, orig_image = cam.read()

        i += 1

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    cam.release()

    print("Angle 1", Angle1)
    print("Angle 2", Angle2)
    print("Angle 3", Angle3)
    print("Angle 4", Angle4)

    dct = {
        'Right Hand' : Angle1,
        'Left Hand' : Angle2,
        'Right Leg' : Angle3,
        'Left Leg' : Angle4
        }

    data = pd.DataFrame(dct)
    data.to_csv("CSV/data.csv")
    
    lis = [i for i in range(len(Angle1))]
    plotting(lis, Angle1,'r', 'RH', 'Right Hand', "plotimages/Right_Hand.jpg")
    plotting(lis, Angle2,'b', 'LH', 'Left Hand', "plotimages/Left_Hand.jpg")
    plotting(lis, Angle3,'k', 'RL', 'Right leg', "plotimages/Right_Leg.jpg")
    plotting(lis, Angle4,'yellow','LL', "Left Leg", "plotimages/Left_Leg.jpg")

    convert_video('/home/saireddy/Desktop/Flask/OrbitPose/videos/output/pose8.avi', '/home/saireddy/Desktop/Flask/OrbitPose/videos/output/pose8.mp4')

video_cap()    
    


