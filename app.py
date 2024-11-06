from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests
import os
from geopy.geocoders import Nominatim
from shapely.geometry import shape, Point

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://192.168.100.132:5000"}})
CORS(app)

# Inicializar el geocodificador
geolocator = Nominatim(user_agent="geoapiExercises")

# Cargar el archivo GeoJSON
geojson_path = 'cobertura.geojson'
with open(geojson_path) as f:
    geojson_data = json.load(f)

# Obtener la clave de API desde las variables de entorno
LOCATIONIQ_API_KEY = os.getenv('LOCATIONIQ_API_KEY', 'pk.281655617a50bb1e5e1d55a6149393d8')

@app.route('/cobertura', methods=['GET'])
def get_cobertura():
    return jsonify(geojson_data)

@app.route('/verificar', methods=['POST'])
def verificar():
    direccion = request.json.get('direccion')
    coords = request.json.get('coords')

    if direccion is None and coords is None:
        return jsonify({'error': 'No se proporcionó dirección o coordenadas.'}), 400

    if coords:
        lat, lng = coords['lat'], coords['lng']
        point = Point(float(lng), float(lat))
    else:
        # Obtener coordenadas de la dirección usando LocationIQ
        geocode_url = f'https://us1.locationiq.com/v1/search.php?key={LOCATIONIQ_API_KEY}&q={direccion}&format=json&country=PE'
        response = requests.get(geocode_url)

        if response.status_code != 200:
            return jsonify({'error': 'Error al comunicarse con el servicio de geocodificación.'}), response.status_code

        data = response.json()

        if not data:
            return jsonify({'error': 'Dirección o lugar no encontrado.'}), 404

        location = data[0]
        point = Point(float(location['lon']), float(location['lat']))

    # Verificar si el punto está dentro de las zonas del GeoJSON
    for feature in geojson_data['features']:
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            return jsonify({
                'dentro': True,
                'mensaje': 'Cobertura disponible.',
                'coords': {'lat': point.y, 'lng': point.x}
            })

    return jsonify({'dentro': False, 'mensaje': 'La dirección no está dentro de la zona.'})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
