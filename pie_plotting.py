import matplotlib.pyplot as plt

def pie_plot(Angle1,Angle2,Angle3,Angle4, filename):
    labels = 'Right_Hand', 'Left_Hand', 'Right_Leg', 'Left_Leg'
    sizes = [len(Angle1), len(Angle2), len(Angle3), len(Angle4)]
    maxi = max(sizes)

    explode = []
    
    for i in range(len(sizes)):
        if sizes[i] == maxi:
            explode.append(0.1)
        else:
            explode.append(0)
            
    explode = tuple(explode)  
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.axis('equal')
    plt.savefig(filename)
    plt.show()
