import os
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load credentials from environment
CLOUD_ID = os.environ.get("ELASTIC_CLOUD_ID")
ELASTIC_USER = os.environ.get("ELASTIC_USERNAME")
ELASTIC_PASS = os.environ.get("ELASTIC_PASSWORD")

es = Elasticsearch(
    cloud_id=CLOUD_ID,
    basic_auth=(ELASTIC_USER, ELASTIC_PASS)
)

# Serve index.html when accessing "/"
@app.route('/')
def serve_index():
    return send_file('index.html')

# Location API endpoint
@app.route('/locations')
def get_locations():
    location_type = request.args.get('type')
    if not location_type:
        return jsonify({"error": "Missing 'type' parameter"}), 400

    query = {
        "size": 1000,
        "query": { "match_all": {} }
    }

    try:
        response = es.search(index=location_type, body=query)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    features = []
    for hit in response['hits']['hits']:
        src = hit['_source']
        loc = src.get('location')
        coords = None

        # ✅ handle lat/lon object
        if isinstance(loc, dict) and 'lat' in loc and 'lon' in loc:
            coords = [loc['lon'], loc['lat']]  # geoJSON expects [lon, lat]

        if coords:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": coords
                },
                "properties": {
                    "name": src.get('place_name', 'No name'),
                    "address": src.get('address', ''),
                    "level": src.get('level', ''),  # Added level field here
                    "description": src.get('description', '')
                }
            })

    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
