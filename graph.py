import os
from processing import plotting
from pie_plotting import pie_plot

def plot(Angle1, Angle2, Angle3, Angle4):
    
    try:
        if os.path.exists("plotimages/Images"):
            root, dirs, files = next(os.walk("plotimages/"))
            length = len(dirs)
            os.mkdir("plotimages/Images{}".format(length+1))
            if not os.listdir("plotimages/Images{}".format(length+1)):
                os.chdir("plotimages/Images{}".format(length+1))
                plotting([i for i in  range(len(Angle1))],
                             Angle1,'r', 'RH', 'Right Hand', "Right_Hand1.jpg")
                plotting([i for i in  range(len(Angle2))],
                             Angle2,'b', 'LH', 'Left Hand', "Left_Hand1.jpg")
                plotting([i for i in  range(len(Angle3))],
                             Angle3,'k', 'RL', 'Right leg', "Right_Leg1.jpg")
                plotting([i for i in  range(len(Angle4))],
                             Angle4,'yellow','LL', "Left Leg", "Left_Leg1.jpg")
                pie_plot(Angle1, Angle2, Angle3, Angle4, "Demographic.jpg")
        else:
            os.mkdir("plotimages/Images")
            if not os.listdir("plotimages/Images"):
                os.chdir("plotimages/Images")
                plotting([i for i in  range(len(Angle1))],
                             Angle1,'r', 'RH', 'Right Hand', "Right_Hand1.jpg")
                plotting([i for i in  range(len(Angle2))],
                             Angle2,'b', 'LH', 'Left Hand', "Left_Hand1.jpg")
                plotting([i for i in  range(len(Angle3))],
                             Angle3,'k', 'RL', 'Right leg', "Right_Leg1.jpg")
                plotting([i for i in  range(len(Angle4))],
                             Angle4,'yellow','LL', "Left Leg", "Left_Leg1.jpg")
                pie_plot(Angle1, Angle2, Angle3, Angle4, "Demographic.jpg")
                
    except Exception as e:
        print("Exception Found:", e)


        
        


