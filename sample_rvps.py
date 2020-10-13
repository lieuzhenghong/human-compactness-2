from docopt import docopt
import geopandas as gpd
import pandas as pd
import random


def sample_rvps(cdb, STATE_CODE, DEM_RVPS, REP_RVPS, SAMPLE_SIZE):
    '''
    This function reads in three files: congressional data, and two RVP files.
    It finds all the RVPs within the state boundaries and takes a random
    sample. Returns a DataFrame of RVPs with geometry in equidistant projection.
    '''

    dems = gpd.read_file(DEM_RVPS)
    reps = gpd.read_file(REP_RVPS)

    dems["party"] = "D"
    reps["party"] = "R"

    # Append Democrats to Republicans to get all VRPs
    all_rvps = dems.append(reps)
    all_rvps["pd"] = 0

    # Make a copy so we do not set values on a copy of a slice
    # We will set values of democrat and republican later
    cdb_state = cdb.query(f"STATEFP == '{STATE_CODE}'").copy()

    # Convert to WGS84
    all_rvps = all_rvps.to_crs({'init': 'epsg:4326'})
    # print(all_rvps[:10])

    # Do a spatial join to get all the RVPs that are in the state
    # All the RVPs should be in the state
    points_in_state = gpd.sjoin(all_rvps, cdb_state, how="inner", op='within')
    # print(points_in_state[:10])

    # Now that we've got all the points in the state, let's try and convert back
    # to an equidistant projection

    points_in_state_eqd = points_in_state.to_crs({'proj': 'eqdc', 'lat_0': 0, 'lon_0': 0, 'lat_1':
                                                  20, 'lat_2': 60, 'x_0': 0, 'y_0': 0, 'datum': 'NAD83', 'units': 'm',
                                                  'no_defs': True})

    # Now that we have the equidistant projection, let's try to calculate
    # Euclidean distances to and from all points.

    # Downsample and return
    points_downsampled = points_in_state_eqd.sample(
        SAMPLE_SIZE, random_state=0)
    points_downsampled = points_downsampled.sort_index()
    points_downsampled.reset_index(inplace=True)

    return points_downsampled
