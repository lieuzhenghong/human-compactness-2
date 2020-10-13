# from docopt import docopt
import geopandas as gpd
import pandas as pd
import random

def sample_rvps(DEM_RVPS, REP_RVPS, SAMPLE_SIZE):
    '''
    This function reads in two files, both RVP files.
    It takes a random sample of size SAMPLE_SIZE and 
    returns a DataFrame of RVPs with geometry in WGS84.
    '''

    dems = gpd.read_file(DEM_RVPS)
    reps = gpd.read_file(REP_RVPS)

    dems["party"] = "D"
    reps["party"] = "R"

    # Append Democrats to Republicans to get all VRPs
    all_rvps = dems.append(reps)

    # Convert to WGS84
    all_rvps = all_rvps.to_crs({'init': 'epsg:4326'})
    
    # Downsample and return
    points_downsampled = all_rvps.sample(
        SAMPLE_SIZE, random_state=0) # this ensures that the RVPs are consistent across runs
    points_downsampled = points_downsampled.sort_index()
    points_downsampled.reset_index(inplace=True)

    return points_downsampled

def concatenate_rvps(DEM_RVPS, REP_RVPS):
    '''
    This function reads in two files, both RVP files.
    It combines the DEM and REP RVPs and returns a 
    GeoDataFrame of RVPs with geometry in WGS84.
    '''

    dems = gpd.read_file(DEM_RVPS)
    reps = gpd.read_file(REP_RVPS)

    dems["party"] = "D"
    reps["party"] = "R"

    # Append Democrats to Republicans to get all VRPs
    all_rvps = dems.append(reps)

    # Convert to WGS84
    all_rvps = all_rvps.to_crs({'init': 'epsg:4326'})

    return all_rvps

def find_rvps_in_region(gdf, rvps):
    '''
    This function reads in a GeoDataFrame for our region and
    our RVPs GeoDataFrame. It converts the GeoDataFrame to geometry 
    WGS84 to match our RVPs GeoDataFrame, and then does a
    spatial join to return a GeoDataFrame of all RVPs within 
    the region.
    '''
    
    # Convert to WGS84
    gdf = gdf.to_crs({'init': 'epsg:4326'})
    
    # Do a spatial join to get all the RVPs that are in the region
    # All the RVPs should be in the region
    points_in_region = gpd.sjoin(rvps, gdf, how="inner", op='within')

    return points_in_region
