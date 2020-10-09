import json
from timeit import default_timer as timer


def duration_between(tract_id, other_id, duration_dict):
    '''Gets the sum of driving durations between one tract and another'''

    #print(f'Getting the driving duration between {tract_id} and {other_id}')

    tract_id = str(tract_id)
    other_id = str(other_id)

    if tract_id not in duration_dict:
        # Don't raise value error. Some tracts have no points in them
        #print(f'Tract_id {tract_id} not in duration dictionary')
        return 0
    elif other_id not in duration_dict[tract_id]:
        #print(f'{tract_id} doesn\'t have {other_id} in its duration dictionary')
        return 0
    else:
        return duration_dict[tract_id][other_id]


def calculate_knn_of_all_points_in_district(dmx, all_districts, tract_dict, tract_to_district_mapping):
    '''
    all_districts is a Set of district_ids.

    tract_dict:
        {
            tract_id: {
                'geoid': GEOID,
                'pop': Int,
                'pfs': List[Float],
                'vrps': List[PointIDs]
            }
        }

    tract_to_district_mapping:
        {
            tract_id: DistrictID
        }
    '''

    #print('Calculating KNN durations for all points in current district assignment ...')

    points_in_each_district = {}
    num_points_in_each_district = {}
    point_to_district_mapping = {}
    sum_of_knn_distances_in_each_district = {}

    # Initialise points_in_districts so we don't have to check for existence condition
    for district_id in all_districts:
        points_in_each_district[district_id] = []
        num_points_in_each_district[district_id] = []
        sum_of_knn_distances_in_each_district[district_id] = 0

    # get all points in a certain district and form a mapping of points to district
    # so now we have the forward mapping, point-> district, as well as the inverse
    # mapping, district -> points
    for tract_id in tract_to_district_mapping:
        district_id = tract_to_district_mapping[tract_id]
        # print(f"Printing tract {tract_id}")
        # print(tract_dict[tract_id])
        points_in_each_district[district_id] += tract_dict[tract_id]['vrps']

        for point_id in tract_dict[tract_id]['vrps']:
            point_to_district_mapping[point_id] = district_id

    # get number of points in each district
    for district_id in all_districts:
        num_points_in_each_district[district_id] = len(
            points_in_each_district[district_id])

    #print(f'Number of points in each district: {num_points_in_each_district}')

    # Read duration dict line by line
    # Each line corresponds to a specific point_id

    ptdm = point_to_district_mapping

    for point_id in ptdm:
        district_id = ptdm[point_id]
        K = num_points_in_each_district[district_id]
        assert(K < 3000)
        #print(district_id, point_id, K)
        # print(len(dmx))  # 14000
        # print(len(dmx[0]))  # 3000
        # print(len(dmx[point_id]))  # 3000
        # print(dmx[point_id][K])  # OK
        sum_of_knn_distances_in_each_district[district_id] += dmx[point_id][K]

    return sum_of_knn_distances_in_each_district


def calculate_human_compactness(duration_dict, tract_dict, dmx, partition):
    '''
    Given the Census Tract duration dict and an assignment from IDs,
    calculate the human compactness of every district in the plan

    The duration dict is in the following format:
    {
        tractid: {tractid: distance, ... },
        tractid: {tractid: distance, ...},
        ...
    }
    tract_dict:
    {
        tract_id: {
            'geoid': GEOID,
            'pop': Int,
            'pfs': List[Float],
            'vrps': List[PointIDs]
        }
    }

    DMX:

    Partition:

    Maintain a total sum as a tally
    Maintain an array of tracts in each district

    For each tract in assignment, check which district it comes from. Then
    add both itself and everyone else in the district to the total human
    compactness sum.
    '''

    # O(n^2) runtime

    total_durations = {}
    total_knn_dds = {}
    tracts_in_districts = {}
    all_districts = set([])

    hc_scores = {}

    for tract_id in partition.graph.nodes:
        district_id = partition.assignment[tract_id]
        all_districts.add(district_id)

        # Fill up dictionary of tracts in a specific district
        if district_id not in tracts_in_districts:
            tracts_in_districts[district_id] = [tract_id]
        else:
            tracts_in_districts[district_id].append(tract_id)

        # Add to the total duration sum. Notice we append to
        # tracts_in_districts first: this is so that we get the sum of driving
        # distances from a tract to itself as well, which makes sense

        # print(
        #    f"Getting pairwise distances between {tract_id} and {tracts_in_districts[district_id]}")

        for other_tract_id in tracts_in_districts[district_id]:
            if district_id not in total_durations:
                total_durations[district_id] = duration_between(
                    tract_id, other_tract_id, duration_dict)
                total_durations[district_id] += duration_between(
                    other_tract_id, tract_id, duration_dict)
            else:
                total_durations[district_id] += duration_between(
                    tract_id, other_tract_id, duration_dict)
                total_durations[district_id] += duration_between(
                    other_tract_id, tract_id, duration_dict)

        # We've double-counted the last self-distance: subtract away

        assert(tract_id == other_tract_id)
        total_durations[district_id] -= duration_between(
            other_tract_id, tract_id, duration_dict)

    # Now we've got the total durations, divide by the sum of all
    # the knns. We have the sums by tract: all that remains is to
    # aggregate by district.
    start = timer()

    total_knn_dds = calculate_knn_of_all_points_in_district(dmx, all_districts,
                                                            tract_dict, partition.assignment)

    end = timer()

    #print(f"Time taken to get KNN durations: {end-start}")

    # OK, so now we have the sum of point-to-point driving
    # durations in a district, and also the sum of KNN dds
    # in a district. Last step is to divide knn_dd by total_durations
    # to get the final human compactness score.

    #print(f"Total KNN DDs: {total_knn_dds}")
    #print(f"Total DDs in district: {total_durations}")

    for district_id in all_districts:
        hc_scores[district_id] = total_knn_dds[district_id] / \
            total_durations[district_id]

    # print(f"HC scores: {hc_scores}")

    return hc_scores


def build_knn_sum_duration_matrix(K, DM_PATH, SAVE_FILE_TO):
    '''
    Given a point matrix in DM_PATH, builds and saves a knn_sum_duration
    matrix to parameter SAVE_FILE_TO, where matrix[i][j] is the sum of
    distances from point i to its j closest neighbours.
    '''
    with open(DM_PATH, 'rt') as fh:
        with open(f'{SAVE_FILE_TO}', 'w') as outfile:
            line = fh.readline()
            # This is currently looking at the durations from point i to all other points
            i = 0
            while line:
                # Get the distances from point i; two spaces is not a typo
                dist = [float(x) for x in line.split('  ')]
                dd_sum = []

                if (i % 1000 == 0):
                    print(f'Now processing line {i}..')

                sorted_dist = sorted(dist)
                j = 0
                while j < K:
                    if j == 0:
                        dd_sum.append(sorted_dist[0])
                    else:
                        dd_sum.append(dd_sum[-1] + sorted_dist[j])
                    j += 1

                # print(sorted_dist[:50])
                # print(dd_sum[:50])
                outfile.writelines([f" {x:.2f} " for x in dd_sum])
                outfile.write('\n')
                i += 1
                line = fh.readline()


def convert_point_distances_to_tract_distances(pttm, DM_PATH, SAVE_FILE_TO):
    '''Returns a JSON file giving driving durations from all points in the Census Tract
    to all other points in every other Census Tract.
    Takes in three things:

        1. A mapping from points to tracts (Dict[PointId : TractId]
        2. The distance matrix file path
        3. The path to save the output tract distance file to

    Reads line by line
    Returns a JSON file with the following schema:
    {
        tractid: {tractid: distance, ... },
        tractid: {tractid: distance, ...},
        ...
    }
    Each entry in the dictionary is the sum of driving durations from each point in
    the tract to each other point in the tract.

    Note that the duration from tract_id to tract_id can (in fact is almost always nonzero)
    because it measures the sum of durations from all points in the tract
    '''
    tract_distances = {}

    with open(DM_PATH, 'rt') as fh:
        line = fh.readline()
        # This is currently looking at the durations from point i to all other points
        i = 0
        while line:
            # Get the distances from point i; two spaces is not a typo
            dist = [float(x) for x in line.split('  ')]
            # Very rarely, points may not lie within tracts. This is strange, but we'll ignore it
            print(f'Now processing line {i}..')
            if i not in pttm:
                print(f'Point ID not in point_to_tract_mapping: {i}')
            # Otherwise, update the tract-pairwise-distance matrix with the pointwise distances
            else:
                for j in range(len(dist)):
                    if j not in pttm:
                        print(f'Point ID not in point_to_tract_mapping: {j}')
                    elif pttm[i] not in tract_distances:
                        tract_distances[pttm[i]] = {pttm[j]: dist[j]}
                    elif pttm[j] not in tract_distances[pttm[i]]:
                        tract_distances[pttm[i]][pttm[j]] = dist[j]
                    else:
                        tract_distances[pttm[i]][pttm[j]] += dist[j]
                    # print(tract_distances)
            i += 1
            line = fh.readline()

    # Save tract matrix to file
    with open(f'{SAVE_FILE_TO}', 'w') as f:
        f.write(json.dumps(tract_distances))


def read_tract_duration_json(DD_PATH):
    with open(DD_PATH) as f:
        return(json.load(f))
