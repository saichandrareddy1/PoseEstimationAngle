import pandas as pd
import numpy as np
import os


def csv_create(Angle1, Angle2, Angle3, Angle4):
    
    if os.path.isfile("CSV/data.csv"):
        path, dirs, files = next(os.walk("CSV/"))
        file_count = len(files)
        lis = [len(Angle1), len(Angle2), len(Angle3), len(Angle4)]
        maxi = max(lis) 
        if len(Angle1) == maxi and len(Angle2) == maxi and len(Angle3) == maxi and len(Angle4) == maxi:
            dct = {
                'Right Hand' : Angle1,
                'Left Hand' : Angle2,
                'Right Leg' : Angle3,
                'Left Leg' : Angle4
                }
            data = pd.DataFrame(dct)
            data.to_csv("CSV/data{}.csv".format(file_count+1))
        else:
             print("SOrry NOt valid Videos is uploaded")

    else:
        lis = [len(Angle1), len(Angle2), len(Angle3), len(Angle4)]
        maxi = max(lis)
        if len(Angle1) == maxi and len(Angle2) == maxi and len(Angle3) == maxi and len(Angle4) == maxi:
            dct = {
                'Right Hand' : Angle1,
                'Left Hand' : Angle2,
                'Right Leg' : Angle3,
                'Left Leg' : Angle4
                }
            data = pd.DataFrame(dct)
            data.to_csv("CSV/data.csv")
        else:
             print("SOrry NOt valid Videos is uploaded")


A = [1, 2, 3, 4, 5, 6, 7,9,0]
a1 = [1, 2, 3, 4, 5, 6, 7,9,0]
a3 = [1, 2, 3, 4, 5, 6, 7,9,0]
a4 = [1, 2, 3, 4, 5, 6, 7,9,0]
csv_create(A, a1, a3, a4)

    
