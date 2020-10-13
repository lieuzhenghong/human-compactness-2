import requests
import numpy as np
from typing import Dict, Tuple, List, NewType


Point = NewType('Point', Tuple[float, float])


def read_duration_matrix_from_file(filename):
    dds = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            #print([x for x in line.split('  ')])
            dds.append([float(x) for x in line.split('  ')])
            # print(dds[-1])
    return dds


def write_duration_matrix_to_file(duration_matrix, filename):
    with open(filename, 'w') as f:
        for row in duration_matrix:
            f.writelines([f" {x} " for x in row])
            f.write('\n')


def all_driving_durations(df, matrix_size: int):
    '''
    Should take in a 
    Returns a NxN matrix, dds, with all point-to-point driving durations
    '''
    try:
        num_rows = df.shape[0]
        dds = np.zeros((num_rows, num_rows), dtype=float)
        print(f"Assigned an array of size {dds.size}")
    except:
        print("Out of memory: trying to assign too big of an array")
        return
    # Now let's use successive distance matrices to fill in the array
    # I will rewrite this to be parallelisable in the far future.
    # Note that I always mutate non-overlapping sections of the array
    # Make sure we don't have any leftovers
    assert(num_rows % matrix_size == 0)
    all_points = df['geometry']
    for source_start in range(0, num_rows, matrix_size):
        for dest_start in range(0, num_rows, matrix_size):
            print(source_start, dest_start)
            driving_durations = distance_matrix(all_points, source_start,
                                                dest_start, matrix_size)
            # driving_durations is a list of lists
            # each sublist is driving times from point to all other points
            for idx, row in enumerate(driving_durations):
                dds[source_start+idx][dest_start:dest_start+matrix_size] = row
    # print(dds)
    return dds


def distance_matrix(points: List[Point], source_start: int, dest_start: int, matrix_size: int):
    ''' Returns a list of distances from and to all points '''
    assert(len(points) > 0)
    assert(matrix_size > 0)
    assert(source_start + matrix_size <= len(points))
    assert(dest_start + matrix_size <= len(points))
    string = ""
    source_string = ""
    dest_string = ""
    for point in points:
        string += f"{round(point.x, 4)},{round(point.y, 4)};"
    for i in range(matrix_size):
        source_string += f"{source_start+i};"
        dest_string += f"{dest_start+i};"

    string = string[:-1]  # delete trailing semicolon
    source_string = source_string[:-1]  # delete trailing semicolon
    dest_string = dest_string[:-1]  # delete trailing semicolon

    # print(string)
    # print(source_string)
    # print(dest_string)

    request_string = f"http://localhost:5000/table/v1/driving/{string}?sources={source_string}&destinations={dest_string}&annotations=duration,distance"
    r = requests.get(request_string)
    durations = r.json()['durations']
    assert(len(durations) == len(durations[0]))
    #driving_distances_to_points = list(zip(points, durations))
    # print(driving_distances_to_points[:10])
    # return driving_distances_to_points
    return durations
