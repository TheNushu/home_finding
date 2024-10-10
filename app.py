from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
from fuzzywuzzy import process

app = Flask(__name__)

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

@app.route('/', methods=['GET', 'POST'])
def handle_requests():
    if request.method == 'POST':
        city = request.form.get('city', '')
        if city:
            city_info = get_city_info(city)
            return jsonify({'city_info': city_info})
        return jsonify({})
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)