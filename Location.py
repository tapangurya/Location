from flask import Flask, request, render_template
from opencage.geocoder import OpenCageGeocode
import folium
import json
import os
from datetime import datetime

app = Flask(__name__)

API_KEY = "8eec8ce32a0a47bbb5497ef7d58a9baa"
DATA_FILE = os.path.join("data", "location.json")


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

    # ---------- SAVE TO JSON ----------
    entry = {
        "timestamp": datetime.now().isoformat(),
        "city": city,
        "latitude": lat,
        "longitude": lng,
        "ip": request.remote_addr
    }

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

    with open(DATA_FILE, "r+") as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=4)

    # ---------- MAP ----------
    m = folium.Map(location=[lat, lng], zoom_start=15)
    folium.Marker(
        [lat, lng],
        popup=f"<b>City:</b> {city}<br><b>Lat:</b> {lat}<br><b>Lng:</b> {lng}",
        icon=folium.Icon(color="blue", icon="map-marker")
    ).add_to(m)

    m.save("templates/map.html")

    return render_template("map.html")


if __name__ == "__main__":
    app.run(debug=True)
