import numpy as np

def read_duration_matrix_from_file(filename):
    dds = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            dds.append([float(x) for x in line.split('  ')])
    return dds

def get_KNN_indices(pairwise_matrix, K, i):
    indices = sorted(list(enumerate(pairwise_matrix[i])), key=lambda x:x[1])
    return [index for (index, pairwise_TT) in indices[:K+1]]

def find_APTT_from_point(point, ids, pairwise_matrix):
    APTT = sum([pairwise_matrix[int(point)][int(other_point)] for other_point in ids])
    return APTT / (len(ids) - 1) # there are K+1 ids, including point

def find_APTT_of_region(ids, pairwise_matrix):
    APTT = sum([find_APTT_from_point(point, ids, pairwise_matrix) for point in ids])
    return APTT / len(ids) 

def return_rvp_ids(rvps):
    return [rvps.iloc[i].name for i in range(len(rvps))]

def find_avg_APTT_of_all_balls(ids, pairwise_matrix):
    APTT_of_balls = []
    for point in ids:
        KNNs_of_point = get_KNN_indices(pairwise_matrix, len(ids), point)
        APTT_of_ball = find_APTT_of_region(KNNs_of_point, pairwise_matrix)
        APTT_of_balls.append(APTT_of_ball)
    return np.mean(APTT_of_balls)