from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import atexit
import shutil
import numpy as np
import pandas as pd
from fuzzywuzzy import process

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Load the city data
DATA_NAME = "cities/worldcities.csv"
city_data = pd.read_csv(DATA_NAME)

def cleanup_temp_folder():
    """Delete the temporary upload folder and its contents"""
    shutil.rmtree(app.config['UPLOAD_FOLDER'], ignore_errors=True)

# Register the cleanup function to be called on exit
atexit.register(cleanup_temp_folder)

def get_image_metadata(image_path):
    from PIL import Image
    from PIL.ExifTags import TAGS
    
    image = Image.open(image_path)
    exif_data = {}
    if hasattr(image, '_getexif'):
        exif = image._getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = str(value)
    return exif_data

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
        response = {}
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                # Clean up previous uploads
                for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Get metadata
                metadata = get_image_metadata(file_path)
                response['filename'] = filename
                response['metadata'] = metadata
        
        # Handle city lookup
        city = request.form.get('city', '')
        if city:
            city_info = get_city_info(city)
            response['city_info'] = city_info
        
        return jsonify(response)
    
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)