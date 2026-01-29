from flask import Flask, request, render_template, jsonify
from opencage.geocoder import OpenCageGeocode
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os

app = Flask(__name__)

# --- CONFIGURATION ---
# Load environment variables
load_dotenv()

DB_NAME = "location_db"
COLLECTION_NAME = "locations"

# --- MongoDB Connection ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/location", methods=["POST"])
def location():
    try:
        # 1. Get coordinates
        lat = float(request.form.get("lat"))
        lng = float(request.form.get("lng"))

        # 2. Reverse Geocoding
        geocoder = OpenCageGeocode(API_KEY)
        result = geocoder.reverse_geocode(lat, lng)

        if not result:
            city = "Unknown"
        else:
            components = result[0].get("components", {})
            city = (
                components.get("city")
                or components.get("town")
                or components.get("village")
                or components.get("suburb")
                or components.get("state")
                or "Unknown"
            )

        # 3. Prepare document
        document = {
            "timestamp": datetime.utcnow(),
            "city": city,
            "latitude": lat,
            "longitude": lng,
            "ip": request.headers.get("X-Forwarded-For", request.remote_addr)
        }

        # 4. Insert into MongoDB
        collection.insert_one(document)

        # 5. Response
        return jsonify({
            "status": "success",
            "message": "Location saved successfully",
            "city": city,
            "coords": {"lat": lat, "lng": lng}
        }), 200

    except Exception as e:
        print(e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
