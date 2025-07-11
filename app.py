from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from elasticsearch import Elasticsearch

app = Flask(__name__)
CORS(app)

# Elasticsearch setup
es = Elasticsearch(
    cloud_id="Demo_Cluster:YXAtc291dGhlYXN0LTIuYXdzLmZvdW5kLmlvOjQ0MyQxNzhiODE1NGZjNjc0MDQ5YTEwMGZhMWM1N2E4M2YyNCRlM2UzOWI2YTcyNDI0OGI2ODEwMzRjMjNjOTZlNmRiNQ==",
    basic_auth=("resume_search", "resumesearch")
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
