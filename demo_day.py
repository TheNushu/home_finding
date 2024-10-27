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
import os

# Load the merged exoplanets data
merged_exoplanets = pd.read_csv('merged_exoplanets.csv')

cities = {
    "Sydney": {"lat": -33.8688, "lon": 151.2093},
    "Helsinki": {"lat": 60.1699, "lon": 24.9384},
    "New York": {"lat": 40.7128, "lon": -74.0060}
}

observer_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def find_visible_exoplanets(observer_location, observer_time, df_exoplanets):
    observer = EarthLocation(lat=observer_location['lat'] * u.deg,
                             lon=observer_location['lon'] * u.deg)
    obs_time = Time(observer_time)

    sky_coords = SkyCoord(ra=df_exoplanets['ra'].values * u.deg,
                          dec=df_exoplanets['dec'].values * u.deg)

    altaz_frame = AltAz(obstime=obs_time, location=observer)
    altaz_coords = sky_coords.transform_to(altaz_frame)

    visible_exoplanets = df_exoplanets[altaz_coords.alt.deg > 0]
    return visible_exoplanets

def process_visibility(args):
    observer_location, observer_time, df_exoplanets = args
    return find_visible_exoplanets(observer_location, observer_time, df_exoplanets)

def find_exoplanets_parallel(observer_location, observer_time, df_exoplanets):
    num_cores = cpu_count()
    chunks = np.array_split(df_exoplanets, num_cores)

    args = [(observer_location, observer_time, chunk) for chunk in chunks]

    with Pool(num_cores) as pool:
        visible_exoplanets_chunks = pool.map(process_visibility, args)

    visible_exoplanets = pd.concat(visible_exoplanets_chunks)
    return visible_exoplanets

def plot_visible_exoplanets(visible_exoplanets, city_name):
    ra_rad = np.radians(visible_exoplanets['ra'].values) - np.pi
    dec_rad = np.radians(visible_exoplanets['dec'].values)
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111, projection="mollweide")

    ax.scatter(ra_rad, dec_rad, s=10, color='goldenrod', marker=MarkerStyle(marker='*'), label='Visible exoplanets')
    ax.set_title(f'Visible Exoplanets in {city_name} now')
    ax.set_xlabel('Right Ascension (radians)')
    ax.set_ylabel('Declination (radians)')
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, f'visible_exoplanets_{city_name}.png')
    
    plt.savefig(image_path)
    plt.close(fig)

    print(f"Image saved as: {image_path}")

def main():

    for city, location in cities.items():
        visible_exoplanets = find_exoplanets_parallel(location, observer_time, merged_exoplanets)
        print(f'Number of visible exoplanets in {city}: {len(visible_exoplanets)}')
        plot_visible_exoplanets(visible_exoplanets, city)

if __name__=="__main__":
    main()