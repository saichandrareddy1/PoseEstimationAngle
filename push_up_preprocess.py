import math
import numpy as np
from scipy.ndimage.filters import gaussian_filter
import cv2
import util
import matplotlib.pyplot as plt
from scipy.spatial import distance 


def extract_parts_push(input_image, params, model, model_params):
    multiplier = [x * model_params['boxsize'] / input_image.shape[0] for x in params['scale_search']]

    # Body parts location heatmap, one per part (19)
    heatmap_avg = np.zeros((input_image.shape[0], input_image.shape[1], 19))
    # Part affinities, one per limb (38)
    paf_avg = np.zeros((input_image.shape[0], input_image.shape[1], 38))

    for scale in multiplier:
        image_to_test = cv2.resize(input_image, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        image_to_test_padded, pad = util.pad_right_down_corner(image_to_test, model_params['stride'],
                                                               model_params['padValue'])

        # required shape (1, width, height, channels)
        input_img = np.transpose(np.float32(image_to_test_padded[:, :, :, np.newaxis]), (3, 0, 1, 2))

        output_blobs = model.predict(input_img)

        # extract outputs, resize, and remove padding
        heatmap = np.squeeze(output_blobs[1])  # output 1 is heatmaps
        heatmap = cv2.resize(heatmap, (0, 0), fx=model_params['stride'], fy=model_params['stride'],
                             interpolation=cv2.INTER_CUBIC)
        heatmap = heatmap[:image_to_test_padded.shape[0] - pad[2], :image_to_test_padded.shape[1] - pad[3], :]
        heatmap = cv2.resize(heatmap, (input_image.shape[1], input_image.shape[0]), interpolation=cv2.INTER_CUBIC)

        paf = np.squeeze(output_blobs[0])  # output 0 is PAFs
        paf = cv2.resize(paf, (0, 0), fx=model_params['stride'], fy=model_params['stride'],
                         interpolation=cv2.INTER_CUBIC)
        paf = paf[:image_to_test_padded.shape[0] - pad[2], :image_to_test_padded.shape[1] - pad[3], :]
        paf = cv2.resize(paf, (input_image.shape[1], input_image.shape[0]), interpolation=cv2.INTER_CUBIC)

        heatmap_avg = heatmap_avg + heatmap / len(multiplier)
        paf_avg = paf_avg + paf / len(multiplier)

    all_peaks = []
    peak_counter = 0

    for part in range(18):
        hmap_ori = heatmap_avg[:, :, part]
        hmap = gaussian_filter(hmap_ori, sigma=3)

        # Find the pixel that has maximum value compared to those around it
        hmap_left = np.zeros(hmap.shape)
        hmap_left[1:, :] = hmap[:-1, :]
        hmap_right = np.zeros(hmap.shape)
        hmap_right[:-1, :] = hmap[1:, :]
        hmap_up = np.zeros(hmap.shape)
        hmap_up[:, 1:] = hmap[:, :-1]
        hmap_down = np.zeros(hmap.shape)
        hmap_down[:, :-1] = hmap[:, 1:]

        # reduce needed because there are > 2 arguments
        peaks_binary = np.logical_and.reduce(
            (hmap >= hmap_left, hmap >= hmap_right, hmap >= hmap_up, hmap >= hmap_down, hmap > params['thre1']))
        peaks = list(zip(np.nonzero(peaks_binary)[1], np.nonzero(peaks_binary)[0]))  # note reverse
        peaks_with_score = [x + (hmap_ori[x[1], x[0]],) for x in peaks]  # add a third element to tuple with score
        idx = range(peak_counter, peak_counter + len(peaks))
        peaks_with_score_and_id = [peaks_with_score[i] + (idx[i],) for i in range(len(idx))]

        all_peaks.append(peaks_with_score_and_id)
        peak_counter += len(peaks)

    connection_all = []
    special_k = []
    mid_num = 10

    for k in range(len(util.hmapIdx)):
        score_mid = paf_avg[:, :, [x - 19 for x in util.hmapIdx[k]]]
        cand_a = all_peaks[util.limbSeq[k][0] - 1]
        cand_b = all_peaks[util.limbSeq[k][1] - 1]
        n_a = len(cand_a)
        n_b = len(cand_b)
        # index_a, index_b = util.limbSeq[k]
        if n_a != 0 and n_b != 0:
            connection_candidate = []
            for i in range(n_a):
                for j in range(n_b):
                    vec = np.subtract(cand_b[j][:2], cand_a[i][:2])
                    norm = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])
                    # failure case when 2 body parts overlaps
                    if norm == 0:
                        continue
                    vec = np.divide(vec, norm)

                    startend = list(zip(np.linspace(cand_a[i][0], cand_b[j][0], num=mid_num),
                                        np.linspace(cand_a[i][1], cand_b[j][1], num=mid_num)))

                    vec_x = np.array(
                        [score_mid[int(round(startend[I][1])), int(round(startend[I][0])), 0]
                         for I in range(len(startend))])
                    vec_y = np.array(
                        [score_mid[int(round(startend[I][1])), int(round(startend[I][0])), 1]
                         for I in range(len(startend))])

                    score_midpts = np.multiply(vec_x, vec[0]) + np.multiply(vec_y, vec[1])
                    score_with_dist_prior = sum(score_midpts) / len(score_midpts) + min(
                        0.5 * input_image.shape[0] / norm - 1, 0)
                    criterion1 = len(np.nonzero(score_midpts > params['thre2'])[0]) > 0.8 * len(
                        score_midpts)
                    criterion2 = score_with_dist_prior > 0
                    if criterion1 and criterion2:
                        connection_candidate.append([i, j, score_with_dist_prior,
                                                     score_with_dist_prior + cand_a[i][2] + cand_b[j][2]])

            connection_candidate = sorted(connection_candidate, key=lambda x: x[2], reverse=True)
            connection = np.zeros((0, 5))
            for c in range(len(connection_candidate)):
                i, j, s = connection_candidate[c][0:3]
                if i not in connection[:, 3] and j not in connection[:, 4]:
                    connection = np.vstack([connection, [cand_a[i][3], cand_b[j][3], s, i, j]])
                    if len(connection) >= min(n_a, n_b):
                        break

            connection_all.append(connection)
        else:
            special_k.append(k)
            connection_all.append([])

    # last number in each row is the total parts number of that person
    # the second last number in each row is the score of the overall configuration
    subset = np.empty((0, 20))
    candidate = np.array([item for sublist in all_peaks for item in sublist])

    for k in range(len(util.hmapIdx)):
        if k not in special_k:
            part_as = connection_all[k][:, 0]
            part_bs = connection_all[k][:, 1]
            index_a, index_b = np.array(util.limbSeq[k]) - 1

            for i in range(len(connection_all[k])):  # = 1:size(temp,1)
                found = 0
                subset_idx = [-1, -1]
                for j in range(len(subset)):  # 1:size(subset,1):
                    if subset[j][index_a] == part_as[i] or subset[j][index_b] == part_bs[i]:
                        subset_idx[found] = j
                        found += 1

                if found == 1:
                    j = subset_idx[0]
                    if subset[j][index_b] != part_bs[i]:
                        subset[j][index_b] = part_bs[i]
                        subset[j][-1] += 1
                        subset[j][-2] += candidate[part_bs[i].astype(int), 2] + connection_all[k][i][2]
                elif found == 2:  # if found 2 and disjoint, merge them
                    j1, j2 = subset_idx
                    membership = ((subset[j1] >= 0).astype(int) + (subset[j2] >= 0).astype(int))[:-2]
                    if len(np.nonzero(membership == 2)[0]) == 0:  # merge
                        subset[j1][:-2] += (subset[j2][:-2] + 1)
                        subset[j1][-2:] += subset[j2][-2:]
                        subset[j1][-2] += connection_all[k][i][2]
                        subset = np.delete(subset, j2, 0)
                    else:  # as like found == 1
                        subset[j1][index_b] = part_bs[i]
                        subset[j1][-1] += 1
                        subset[j1][-2] += candidate[part_bs[i].astype(int), 2] + connection_all[k][i][2]

                # if find no partA in the subset, create a new subset
                elif not found and k < 17:
                    row = -1 * np.ones(20)
                    row[index_a] = part_as[i]
                    row[index_b] = part_bs[i]
                    row[-1] = 2
                    row[-2] = sum(candidate[connection_all[k][i, :2].astype(int), 2]) + connection_all[k][i][2]
                    subset = np.vstack([subset, row])

    # delete some rows of subset which has few parts occur
    delete_idx = []
    for i in range(len(subset)):
        if subset[i][-1] < 4 or subset[i][-2] / subset[i][-1] < 0.4:
            delete_idx.append(i)
    subset = np.delete(subset, delete_idx, axis=0)

    return all_peaks, subset, candidate

Angle5 = []
Angle6 = []

Distance5 = []
Distance6 = []

def plotting(leng, Angle, co, le, legend, filename):
        plt.plot(leng, Angle, c = co)
        plt.xlabel("Total frames")
        plt.ylabel("Angle at points")
        plt.legend(le)
        plt.title(legend)
        plt.savefig(filename)
        plt.show()
        
points = []


def dist(Distance):
    
    #print("Distance angle", Distance)
    for i in range(len(Distance)-1):
        #print(Distance)
        c_1 = distance.euclidean(Distance[1], Distance[0])
        a_1 = distance.euclidean(Distance[1], Distance[2])
        b_1 = distance.euclidean(Distance[2], Distance[0])
        #print(c_1, a_1, b_1)
        return c_1, a_1, b_1
    
    else:
        c_1, a_1, b_1 = 0, 0, 0
        return c_1, a_1, b_1

def angle_final5(c_1, a_1, b_1):
        
        val = [c_1, a_1, b_1]
        #print("val ======================", val)

        if len(val) == 3:
                top = c_1**2 + a_1**2 - b_1**2
                down = 2*c_1*a_1
                before = math.acos(top/down)
                theta5 = before * (180/math.pi)
                print("THeta ===========================", theta5)
                Angle5.append(theta5)
                return theta5
        else:
            theta5 = 0.0
            return theta5
                
def angle_final6(c_1, a_1, b_1):
        
        val = [c_1, a_1, b_1]
        #print("val ======================", val)
        if len(val) == 3:
                top = c_1**2 + a_1**2 - b_1**2
                down = 2*c_1*a_1
                before = math.acos(top/down)
                theta6 = before * (180/math.pi)
                print("THeta ===========================", theta6)
                Angle6.append(theta6)
                return theta6
        else:
            theta5 = 0.0
            return theta5
                
                
def draw_push(input_image, all_peaks, subset, candidate, resize_fac=1):
    canvas = input_image.copy()
    global Distance5, Distance6
    global A, B
    global theta5, theta6
    theta5 =  0.0
    theta6 = 0.0
    for i in range(18):
        for j in range(len(all_peaks[i])):
            A = all_peaks[i][j][0] * resize_fac
            B = all_peaks[i][j][1] * resize_fac
            #print(A, B)
            point = all_peaks[i][j][3]
            #print("point =====================", point)

            li = [2, 3, 4]
            if point in li:
                if point == 2:
                    points.append(point)
                    Distance5.append((A, B))
                elif point == 3:
                    points.append(point)
                    Distance5.append((A, B))
                elif point == 4:
                    points.append(point)
                    Distance5.append((A, B))
                    #print("Disatce 1", Distance)
##                    Point1 = Distance5[0]
##                    point_11, point_12 = Point1[0]//2, Point1[1]//2
##                    pointleft = tuple((point_11, point_12))
##                    print(f"{pointleft}")
##
##                    Point2 = Distance5[2]
##                    point_21, point_22 = Point2[0]//2, Point2[1]//2
##                    pointright = tuple((point_21, point_22))
##                    
##                    canvas = cv2.line(canvas, pointleft, pointright, (255, 5, 176), 3)
                    canvas = cv2.line(canvas, Distance5[0] , Distance5[2], (255, 5, 176), 3)
                    c_1, a_1, b_1 = dist(Distance5)
                    #print("======================================", c_1, a_1, b_1)
                    theta5 = str(angle_final5(c_1, a_1, b_1))
                    #print("========================", angle_final5(c_1, a_1, b_1))
                    print("Theta ============", theta5, type(theta5))
                    Distance5.clear()
                    points.clear()
                else:
                    pass
            else:
                pass

            ##RIGHT LEG
            le = [5, 6, 7]
            if point in le:
                if point == 5:
                    points.append(point)
                    Distance6.append((A, B))
                elif point == 6:
                    points.append(point)
                    Distance6.append((A, B))
                elif point == 7:
                    points.append(point)
                    Distance6.append((A, B))
                    #print("Disatce 2", Distance)
##                    Point1_6 = Distance6[0]
##                    point_11_6, point_12_6 = Point1_6[0]//2, Point1_6[1]//2
##                    pointleft_6 = tuple((point_11_6, point_12_6))
##                    print(f"{pointleft_6}")
##
##                    Point2_6 = Distance6[2]
##                    point_21_6, point_22_6 = Point2_6[0]//2, Point2_6[1]//2
##                    pointright_6 = tuple((point_21_6, point_22_6))
##                    print(f"{pointright_6}")
##                    
##                    canvas = cv2.line(canvas, pointleft_6, pointright_6, (255, 5, 176), 3)
                    canvas = cv2.line(canvas, Distance6[0] , Distance6[2], (255, 5, 176), 3)
                    c_1, a_1, b_1 = dist(Distance6)
                    theta6 = str(angle_final6(c_1, a_1, b_1))
                    print("Theta ============", theta6, type(theta6))
                    Distance6.clear()
                    points.clear()
                else:
                    pass
            else:
                pass


            
                
            cv2.circle(canvas, (A, B), 2, util.colors[i], thickness=-1)

    stickwidth = 3

    for i in range(17):
        for s in subset:
            index = s[np.array(util.limbSeq[i]) - 1]
            if -1 in index:
                continue
            cur_canvas = canvas.copy()
            y = candidate[index.astype(int), 0]
            x = candidate[index.astype(int), 1]
            m_x = np.mean(x)
            m_y = np.mean(y)
            length = ((x[0] - x[1]) ** 2 + (y[0] - y[1]) ** 2) ** 0.5
            angle = math.degrees(math.atan2(x[0] - x[1], y[0] - y[1]))
            #if Angle1 > 100 and Angle2 > 100 and Angle3 > 100 and Angle4 > 100:
            if float(theta5) > 170 or float(theta6) > 170:
                polygon = cv2.ellipse2Poly((int(m_y * resize_fac), int(m_x * resize_fac)),(int(length * resize_fac / 2), stickwidth), int(angle), 0, 360, 1)
                cv2.fillConvexPoly(cur_canvas, polygon, util.colors2[i])
                canvas = cv2.addWeighted(canvas, 0.4, cur_canvas, 0.6, 0)
            else:
                polygon = cv2.ellipse2Poly((int(m_y * resize_fac), int(m_x * resize_fac)),(int(length * resize_fac / 2), stickwidth), int(angle), 0, 360, 1)
                cv2.fillConvexPoly(cur_canvas, polygon, util.colors[i])
                canvas = cv2.addWeighted(canvas, 0.4, cur_canvas, 0.6, 0)

    return canvas, theta5, theta6, Angle5, Angle6
