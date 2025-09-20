from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, time

app = Flask(__name__)
CORS(app)

DB = "gps_data.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bus_locations (
            bus_id TEXT,
            lat REAL,
            lon REAL,
            timestamp INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/track", methods=["POST"])
def track():
    data = request.json
    if not data or not all(k in data for k in ("bus_id","lat","lon")):
        return {"error": "invalid data"}, 400
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO bus_locations VALUES (?,?,?,?)",
              (data["bus_id"], data["lat"], data["lon"], int(time.time())))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.route("/latest", methods=["GET"])
def latest():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        SELECT bus_id, lat, lon, timestamp
        FROM bus_locations
        WHERE (bus_id, timestamp) IN (
            SELECT bus_id, MAX(timestamp)
            FROM bus_locations
            GROUP BY bus_id
        )
    """)
    rows = c.fetchall()
    conn.close()
    buses = [{"bus_id": r[0], "lat": r[1], "lon": r[2], "ts": r[3]} for r in rows]
    return jsonify(buses)


@app.route("/", methods=["GET", "POST"])
def traccar_adapter():
    print("\n--- Incoming Request ---")
    print("Method:", request.method)
    print("Args:", dict(request.args))
    print("Form:", dict(request.form))
    print("JSON:", request.get_json(silent=True))
    print("------------------------\n")

    data = request.get_json(silent=True) or {}

    # Traccar JSON format
    device_id = data.get("device_id")
    location = data.get("location", {})
    coords = location.get("coords", {})

    lat = coords.get("latitude")
    lon = coords.get("longitude")

    if device_id and lat and lon:
        print(f"📍 Received from {device_id}: {lat}, {lon}")
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO bus_locations VALUES (?,?,?,?)",
                  (device_id, float(lat), float(lon), int(time.time())))
        conn.commit()
        conn.close()
        return "OK"

    print("⚠️ Missing parameters in request")
    return "Missing parameters", 400





if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
