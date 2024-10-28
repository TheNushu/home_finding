import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from skyfield.api import load
from skyfield.data import hipparcos
from multiprocessing import Pool, cpu_count
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy import units as u
from datetime import datetime, timezone
from matplotlib.markers import MarkerStyle

"""
This code was mainly created in order to achieve the merged_exoplanets.csv
Currently it servers no purpose in the current implementation, but it has some
'history' of how we started the project.
"""

# main flow:
# 1) get the location and time from the website
# 2) construct the sky that the observer sees
#    and find the stars that are visible from the observer's location
# 3) match the stars in the Hipparcos catalog and the stars NASA's exoplanet catalog
# 4) output a subset of the NASA's exoplanet catalog that the user can "see"
# 5) output a plot of the matched stars
# 6) determining habitability
# 7) output a subset of the NASA's exoplanet catalog that is habitable
# 8) data visualization and comparison

with load.open(hipparcos.URL) as f:
    stars = hipparcos.load_dataframe(f)
# only ~0.222% of the ra/decs of the stars are NaNs, so we can just drop them,
# since if they were replaced by the mean/median of the column, it would not really make sense
stars = stars.dropna(subset=['ra_degrees', 'dec_degrees'])

# these need to be modified to be given as input (somehow obtained from the website)
observer_location = {
    'lat': 64.128288,
    'lon': -21.827774
}

observer_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

# exoplanet catalog from:
# https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=PSCompPars
# explanation of columns: 
# https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html#addtldata

exoplanet_catalog = pd.read_csv('PSCompPars.csv', comment='#')
# This is required because the Kepler data is too clustered in one area of the sky, creating an unnecessarily big cluster of stars
#exoplanet_catalog = exoplanet_catalog[exoplanet_catalog['disc_facility'] != 'Kepler']
ra_center = 285
dec_center = 45
radius = 10

ra_radians = np.radians(exoplanet_catalog['ra'])
dec_radians = np.radians(exoplanet_catalog['dec'])
ra_center_rad = np.radians(ra_center)
dec_center_rad = np.radians(dec_center)

def angular_distance(ra1, dec1, ra2, dec2):
    return np.arccos(np.sin(dec1) * np.sin(dec2) + np.cos(dec1) * np.cos(dec2) * np.cos(ra1 - ra2))

distances = angular_distance(ra_radians, dec_radians, ra_center_rad, dec_center_rad)
exoplanet_catalog = exoplanet_catalog[distances > np.radians(radius)]

def find_visible_stars(observer_location, observer_time, df_stars):
    # Observer's EarthLocation (latitude, longitude, and altitude in meters)
    observer = EarthLocation(lat=observer_location['lat'] * u.deg,
                             lon=observer_location['lon'] * u.deg)
    # Observation time in UTC
    obs_time = Time(observer_time)

    # Transform RA/Dec of stars to AltAz frame for the observer
    sky_coords = SkyCoord(ra=df_stars['ra_degrees'].values * u.deg,
                          dec=df_stars['dec_degrees'].values * u.deg)

    altaz_frame = AltAz(obstime=obs_time, location=observer)
    altaz_coords = sky_coords.transform_to(altaz_frame)

    # Filter stars that are above the horizon (alt > 0 degrees)
    visible_stars = df_stars[altaz_coords.alt.deg > 0]
    return visible_stars

# Parallelized function to process star visibility for multiple observers
def process_visibility(args):
    observer_location, observer_time, df_stars = args
    return find_visible_stars(observer_location, observer_time, df_stars)

# Main function to find stars visible from an observer's location
def find_stars_parallel(observer_location, observer_time, df_stars):
    # Split star catalog into chunks for parallel processing
    num_cores = cpu_count()
    chunks = np.array_split(df_stars, num_cores)

    # Create argument list for parallel processing
    args = [(observer_location, observer_time, chunk) for chunk in chunks]

    # Parallel processing using multiprocessing Pool
    with Pool(num_cores) as pool:
        visible_stars_chunks = pool.map(process_visibility, args)

    # Combine results from all chunks
    visible_stars = pd.concat(visible_stars_chunks)
    return visible_stars

# Matching stars in the Hipparcos catalog with stars in NASA's exoplanet catalog
def match_stars_in_chunk(args):
    ra_visible_chunk, dec_visible_chunk, ra_exoplanet, dec_exoplanet, threshold = args
    
    def angular_separation(ra1, dec1, ra2, dec2):
        return np.arccos(np.sin(dec1) * np.sin(dec2) +
                         np.cos(dec1) * np.cos(dec2) * np.cos(ra1 - ra2))

    matched_stars_list = []
    for ra_visible, dec_visible in zip(ra_visible_chunk, dec_visible_chunk):
        separation = angular_separation(ra_visible, dec_visible, ra_exoplanet, dec_exoplanet)
        mask = separation < threshold
        matched_stars = exoplanet_catalog[mask]
        if not matched_stars.empty:
            matched_stars_list.append(matched_stars)

    if matched_stars_list:
        return pd.concat(matched_stars_list, ignore_index=True).drop_duplicates()
    else:
        return pd.DataFrame()

def match_stars(ra_list1, dec_list1):
    num_cores = cpu_count()

    # Split visible stars into chunks for parallel processing
    ra_chunks = np.array_split(np.radians(ra_list1), num_cores)
    dec_chunks = np.array_split(np.radians(dec_list1), num_cores)
    
    ra_exoplanet = np.radians(exoplanet_catalog['ra'].values)
    dec_exoplanet = np.radians(exoplanet_catalog['dec'].values)

    threshold = 0.003

    # Prepare arguments for parallel processing
    args = [(ra_chunk, dec_chunk, ra_exoplanet, dec_exoplanet, threshold) for ra_chunk, dec_chunk in zip(ra_chunks, dec_chunks)]

    # Parallel execution
    with Pool(num_cores) as pool:
        matched_stars_chunks = pool.map(match_stars_in_chunk, args)

    # Combine the results
    matched_stars_df = pd.concat(matched_stars_chunks, ignore_index=True).drop_duplicates()
    return matched_stars_df

def plot_matched_stars(matched_stars_df):
    ra_rad = np.radians(matched_stars_df['ra'].values) - np.pi
    dec_rad = np.radians(matched_stars_df['dec'].values)
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111, projection="mollweide")

    ax.scatter(ra_rad, dec_rad, s=10, color='goldenrod', marker=MarkerStyle(marker='*'), label='Matched stars') # add different color depending on stellar type?
    ax.set_title('Stars that have an exoplanet orbiting them')
    ax.set_xlabel('Right Ascension (radians)')
    ax.set_ylabel('Declination (radians)')
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    plt.savefig('stars_no_kepler.png')
    plt.show()

def plot_and_match_stars(ra_list, dec_list):
    matched_stars = match_stars(ra_list, dec_list)
    #print(len(matched_stars))
    plot_matched_stars(matched_stars)
    return matched_stars

def plot_exoplanets(habitable_filtered):
    ra, dec = np.radians(habitable_filtered['ra']) - np.pi, np.radians(habitable_filtered['dec'])

    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111, projection="mollweide")
    ax.scatter(ra, dec, s=10, color='slateblue', label='Exoplanets')
    
    ax.set_title('Exoplanets with habitability_score > 0.5')
    ax.set_xlabel('Right Ascension (radians)')
    ax.set_ylabel('Declination (radians)')
    ax.grid(True)

    plt.tight_layout()
    plt.legend()
    plt.savefig('exoplanets_no_kepler.png')
    plt.show()

# Habitability index stuff, can be replaced or improved
def habitability_index(exoplanet_data):
    # Earth reference values (normalized to 1)
    earth_values = {
        'temperature': 288,  # in Kelvin
        'radius': 1,      # in 6371km, 1 eart radius
        'density': 5.51,     # in g/cm^3
        'mass': 1,           # in Earth masses
        'orbital_period': 365.25  # in days
    }
    # add columns

    score = 0
    count = 0

    # Temperature
    if not np.isnan(exoplanet_data['pl_eqt']):
        score += np.exp(-abs(exoplanet_data['pl_eqt'] - earth_values['temperature']) / earth_values['temperature'])
        count += 1

    # Radius
    if not np.isnan(exoplanet_data['pl_rade']):
        score += np.exp(-abs(exoplanet_data['pl_rade'] - earth_values['radius']) / earth_values['radius'])
        count += 1

    # Density
    if not np.isnan(exoplanet_data['pl_dens']):
        score += np.exp(-abs(exoplanet_data['pl_dens'] - earth_values['density']) / earth_values['density'])
        count += 1

    # Orbital Period
    if not np.isnan(exoplanet_data['pl_orbper']):
        score += np.exp(-abs(exoplanet_data['pl_orbper'] - earth_values['orbital_period']) / earth_values['orbital_period'])
        count += 1
    
    # Return the average score, normalized to the number of available parameters
    if count > 0:
        return score / count
    else:
        return np.nan  # If no parameters are available


def main():
    visible_stars = find_stars_parallel(observer_location, observer_time, stars)

    ra_list, dec_list = visible_stars['ra_degrees'].values, visible_stars['dec_degrees'].values
    matched_exos = plot_and_match_stars(ra_list, dec_list)
    matched_exos['habitability_score'] = matched_exos.apply(habitability_index, axis=1)

    top_habitable_planets = matched_exos.sort_values(by='habitability_score', ascending=False)
    habitable_planets = top_habitable_planets.dropna(subset=['habitability_score'])
    threshold = 0.5
    habitable_filtered = habitable_planets[habitable_planets['habitability_score'] > threshold]
    
    print(f'Number of habitable planets: {len(habitable_filtered)}')
    plot_exoplanets(habitable_filtered)

    return habitable_filtered

if __name__=="__main__":
    main()
