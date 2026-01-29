from flask import Flask, request, render_template, jsonify
from opencage.geocoder import OpenCageGeocode
import json
import os
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = "8eec8ce32a0a47bbb5497ef7d58a9baa"
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "location.json")

@app.route("/")
def index():
    """Renders the main page with the permission modal."""
    return render_template("index.html")

@app.route("/location", methods=["POST"])
def location():
    """Handles background AJAX requests to save location data."""
    try:
        # 1. Get coordinates from the AJAX request
        lat = float(request.form.get("lat"))
        lng = float(request.form.get("lng"))

        # 2. Reverse Geocoding via OpenCage
        geocoder = OpenCageGeocode(API_KEY)
        result = geocoder.reverse_geocode(lat, lng)

        if not result:
            city = "Unknown"
        else:
            components = result[0].get("components", {})
            # Try to find the best name for the area
            city = (
                components.get("city")
                or components.get("town")
                or components.get("village")
                or components.get("suburb")
                or components.get("state")
                or "Unknown"
            )

        # 3. Prepare the data entry
        os.makedirs(DATA_DIR, exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "city": city,
            "latitude": lat,
            "longitude": lng,
            "ip": request.headers.get("X-Forwarded-For", request.remote_addr)
        }

        # 4. Save to JSON file (Thread-safe-ish logic)
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

        data = []
        with open(DATA_FILE, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate() # Ensure old data is cleared if file size shrinks

        # 5. Return JSON instead of a new page
        return jsonify({
            "status": "success",
            "message": "Location saved successfully",
            "city": city,
            "coords": {"lat": lat, "lng": lng}
        }), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    # Ensure port is pulled from environment for hosting (like Heroku/Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)