from flask import Flask, request, render_template
from opencage.geocoder import OpenCageGeocode
import folium
import json
import os
from datetime import datetime

app = Flask(__name__)

# READ API KEY FROM ENVIRONMENT (IMPORTANT)
API_KEY = os.environ.get("OPENCAGE_API_KEY")

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "location.json")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/location", methods=["POST"])
def location():
    lat = float(request.form["lat"])
    lng = float(request.form["lng"])

    geocoder = OpenCageGeocode(API_KEY)
    result = geocoder.reverse_geocode(lat, lng)

    components = result[0]["components"]
    city = (
        components.get("city")
        or components.get("town")
        or components.get("village")
        or components.get("state")
    )

    # ---------- ENSURE DATA DIRECTORY ----------
    os.makedirs(DATA_DIR, exist_ok=True)

    # ---------- SAVE TO JSON ----------
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "city": city,
        "latitude": lat,
        "longitude": lng,
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr)
    }

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

    with open(DATA_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=4)

    # ---------- MAP ----------
    m = folium.Map(location=[lat, lng], zoom_start=15)
    folium.Marker(
        [lat, lng],
        popup=f"<b>City:</b> {city}<br><b>Lat:</b> {lat}<br><b>Lng:</b> {lng}",
        icon=folium.Icon(color="blue")
    ).add_to(m)

    m.save("templates/map.html")
    return render_template("map.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
