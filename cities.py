import numpy as np
import pandas as pd
from fuzzywuzzy import process
import sys

# Load the city data
DATA_NAME = "cities/worldcities.csv"
city_data = pd.read_csv(DATA_NAME)

def get_city_info(city_name):
    # Use fuzzy matching to find the closest city name
    closest_match = process.extractOne(city_name, city_data['city'])
    if closest_match and closest_match[1] > 80:  # 80% similarity threshold
        matched_city = closest_match[0]
        city_row = city_data[city_data['city'] == matched_city].iloc[0]
        return {
            'city': matched_city,
            'lat': city_row['lat'],
            'lng': city_row['lng'],
            'country': city_row['country'],
            'population': city_row['population'],
            'original_input': city_name
        }
    return None

def print_city_info(result):
    if result:
        print(f"Input: {result['original_input']}")
        print(f"Matched City: {result['city']}")
        print(f"Coordinates: {result['lat']}, {result['lng']}")
        print(f"Country: {result['country']}")
        print(f"Population: {result['population']}")
    else:
        print(f"No match found for {result['original_input']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <city_name>")
        sys.exit(1)

    city_name = " ".join(sys.argv[1:])
    result = get_city_info(city_name)
    print_city_info(result)

# Placeholder for time zone integration
# You would need to add a time zone dataset and integrate it here
# For example:
# def get_time_zone(lat, lng):
#     # Logic to find the time zone based on coordinates
#     pass

# city_data['time_zone'] = city_data.apply(lambda row: get_time_zone(row['lat'], row['lng']), axis=1)