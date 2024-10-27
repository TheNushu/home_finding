from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
from fuzzywuzzy import process
import os
from demo_day import find_exoplanets_parallel, plot_visible_exoplanets
from datetime import datetime, timezone

app = Flask(__name__)

# Load the city data
DATA_NAME = "cities/worldcities.csv"
city_data = pd.read_csv(DATA_NAME)

# Load the merged exoplanets data
merged_exoplanets = pd.read_csv('merged_exoplanets.csv')

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

@app.route('/', methods=['GET', 'POST'])
def handle_requests():
    if request.method == 'POST':
        city = request.form.get('city', '')
        if city:
            city_info = get_city_info(city)
            
            if city_info:
                # Print city name and country
                print(f"City: {city_info['city']}, Country: {city_info['country']}")
                
                # Print coordinates
                print(f"Coordinates: ({city_info['lat']}, {city_info['lng']})")
                
                # Generate the exoplanet image
                observer_location = {'lat': city_info['lat'], 'lon': city_info['lng']}
                observer_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                visible_exoplanets = find_exoplanets_parallel(observer_location, observer_time, merged_exoplanets)
                plot_visible_exoplanets(visible_exoplanets, city_info['city'])
                
                image_filename = f'visible_exoplanets_{city_info["city"]}.png'
                
                return jsonify({
                    'city_info': city_info,
                    'image_filename': image_filename
                })
            else:
                return jsonify({'error': 'City not found'}), 404
        return jsonify({'error': 'No city provided'}), 400
    return render_template('index.html')

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(debug=True)