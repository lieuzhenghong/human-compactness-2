import geopandas as gpd
import human_compactness_utils as hc_utils
import sys
import distance_matrix
import rvp_utils

def read_duration_matrix_from_file(filename):
    dds = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            #print([x for x in line.split('  ')])
            dds.append([float(x) for x in line.split('  ')])
            # print(dds[-1])
    return dds

state_name = 'georgia'
state_fips = '13'
DD_PATH = f'./20_intermediate_files/{state_fips}_{state_name}_tract_dds.json'
DM_PATH = f'./20_intermediate_files/{state_fips}_{state_name}_knn_sum_dd.dmx'
DURATION_DICT = hc_utils.read_tract_duration_json(DD_PATH)
SHAPEFILE_PATH = f'./Data_2000/Shapefiles/ga_2010_cds/ga_2010_cds.shp'
DEM_RVP_PATH = "RVPs/points_D_13_2_10000_run1.shp"
REP_RVP_PATH = "RVPs/points_R_13_2_10000_run1.shp"

# PAIRWISE_DM_PATH = f'./20_intermediate_files/duration_matrix_{state_name}_{state_fips}.dmx'

# pairwise_matrix = read_duration_matrix_from_file(PAIRWISE_DM_PATH)
# print(pairwise_matrix[0][:10])

print("Reading tract shapefile into memory...")
state_shp = gpd.read_file(SHAPEFILE_PATH)
GA_07 = state_shp[state_shp["CD"] == "07"]

print("Reading duration matrix from memory...")
travel_time_matrix = read_duration_matrix_from_file(DM_PATH)

print("Creating RVPs...")
rvps = rvp_utils.sample_rvps(DEM_RVP_PATH, REP_RVP_PATH, 14*1000)
rvps_in_region = rvp_utils.find_rvps_in_region(state_shp, rvps)
rvps_in_GA_07 = rvp_utils.find_rvps_in_region(GA_07, rvps) # 2135 of them

APTT = {}

for i in range(len(rvps_in_GA_07)):
    idx = rvps_in_GA_07.iloc[i].name
    APTT[idx] = travel_time_matrix[idx][len(rvps_in_GA_07)]/len(rvps_in_GA_07)
    print(APTT[idx])
    break

# print(travel_time_matrix[0])
# print(rvps_in_region.shape)
# print(rvps_in_region[:5])
#
# print(rvps_in_GA_07.shape)
# print(rvps_in_GA_07[:5])
