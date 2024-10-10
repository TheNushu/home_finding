from skyfield.api import Topos, load, Star, Angle, wgs84
from skyfield.data import hipparcos
import matplotlib.pyplot as plt
import numpy as np

with load.open(hipparcos.URL) as f:
    stars = hipparcos.load_dataframe(f)

# Helsinki:
latitude = 60.16952
longitude = 24.93545

# try sydney too which is probably different enought from Helsinki:
#latitude2 = -33.865143
#longitude2 = 151.209900

# new york
latitude2 = 40.7128
longitude2 = -74.0060

def get_radecs_from_position(latitude, longitude):
    #location = Topos(latitude_degrees=latitude, longitude_degrees=longitude) # deprecated accprding to the docs; use wgs84.latlon or iers2010.latlon
    location_wgs = wgs84.latlon(latitude, longitude) # gives the same as Topos?

    ts = load.timescale()
    image_time = ts.utc(2023, 9, 15, 21, 30, 0)
    eph = load('de421.bsp')

    observer = eph['earth'] + location_wgs

    ras = []
    decs = []

    # Loop through each star in the catalog
    for index, star in stars.iterrows():
        # Create a Skyfield Star object using the star's Hipparcos data
        hip_star = Star(ra=Angle(degrees=star['ra_degrees']), dec=Angle(degrees=star['dec_degrees'])) # need to use Angle-object
        
        # Calculate the position of the star as seen from the observer
        star_position = observer.at(image_time).observe(hip_star)

        # Calculate the apparent position of the star
        apparent = star_position.apparent()
        # vital for only getting the stars that you can see from the geographic location:
        altitude = apparent.altaz()[0].degrees
        # see "Positions" and "azumuth and altitude from a geographic postion" in the docs

        # stars above horizon
        if altitude > 0:
            ra, dec, distance = apparent.radec()
            ras.append(ra.hours)
            decs.append(dec.degrees)
        # the loop takes like 4 mins

    return ras, decs


ras1, decs1 = get_radecs_from_position(latitude, longitude)
ras2, decs2 = get_radecs_from_position(latitude2, longitude2)

fig, ax = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

# only top 100 stars bc there's a lot of them
ax[0].scatter(ras1[:100], decs1[:100], s=1, color='blue')
ax[0].set_title('RA-Dec from Helsinki')
ax[0].set_xlabel('Right Ascension (hours)')
ax[0].set_ylabel('Declination (degrees)')

ax[1].scatter(ras2[:100], decs2[:100], s=1, color='crimson')
ax[1].set_title('RA-Dec from NY')
ax[1].set_xlabel('Right Ascension (hours)')

plt.tight_layout()
plt.show()

# plotting all the stars would look a bit weird since we'd be plotting 3D coordinates onto a 2D plane, so use a mollweide projection:
fig2, ax2 = plt.subplots(1, 2, figsize=(12, 6), subplot_kw={'projection': 'mollweide'})

ax2[0].scatter(np.radians(ras1)-np.pi, np.radians(decs1), s=1, color='blue')
ax2[0].set_title('RA-Dec from Helsinki')
ax2[0].set_xlabel('Right Ascension (hours)')
ax2[0].set_ylabel('Declination (degrees)')

ax2[1].scatter(np.radians(ras2)-np.pi, np.radians(decs2), s=1, color='crimson')
ax2[1].set_title('RA-Dec from NY')
ax2[1].set_xlabel('Right Ascension (hours)')
plt.tight_layout()
plt.show()

# all stars, no projection
#fig2, ax2 = plt.subplots(1, 2, figsize=(12, 6))

#ax2[0].scatter(ras1, decs1, s=1, color='blue')
#ax2[0].set_title('RA-Dec from Helsinki')
#ax2[0].set_xlabel('Right Ascension (hours)')
#ax2[0].set_ylabel('Declination (degrees)')

#ax2[1].scatter(ras2, decs2, s=1, color='crimson')
#ax2[1].set_title('RA-Dec from NY')
#ax2[1].set_xlabel('Right Ascension (hours)')

#plt.tight_layout()
#plt.show()