import os, json, sqlite3, requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load the hidden variables from the .env file
load_dotenv()

app = Flask(__name__)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"
DB = "ocean_chat.db"

# ── Ocean locations to fetch live data for ─────────────────────────────────
# قائمة شاملة لأهم المحيطات والبحار حول العالم مع إحداثيات تقريبية لمركزها
OCEAN_LOCATIONS = [
    # المحيطات (Oceans)
    {"name": "North Pacific Ocean", "lat": 30.0, "lon": -140.0},
    {"name": "South Pacific Ocean", "lat": -30.0, "lon": -130.0},
    {"name": "North Atlantic Ocean", "lat": 35.0, "lon": -40.0},
    {"name": "South Atlantic Ocean", "lat": -30.0, "lon": -15.0},
    {"name": "Indian Ocean", "lat": -15.0, "lon": 70.0},
    {"name": "Arctic Ocean", "lat": 78.0, "lon": 0.0},
    {"name": "Southern Ocean", "lat": -60.0, "lon": 0.0},

    # البحار في الشرق الأوسط ومحيطه
    {"name": "Red Sea", "lat": 21.0, "lon": 38.0},
    {"name": "Arabian Gulf", "lat": 26.0, "lon": 51.0},
    {"name": "Arabian Sea", "lat": 15.0, "lon": 65.0},
    {"name": "Mediterranean Sea", "lat": 35.0, "lon": 18.0},
    {"name": "Black Sea", "lat": 43.0, "lon": 35.0},
    {"name": "Caspian Sea", "lat": 42.0, "lon": 50.0},

    # بحار عالمية أخرى هامة
    {"name": "Caribbean Sea", "lat": 15.0, "lon": -75.0},
    {"name": "Gulf of Mexico", "lat": 25.0, "lon": -90.0},
    {"name": "Bering Sea", "lat": 58.0, "lon": -175.0},
    {"name": "Sea of Okhotsk", "lat": 55.0, "lon": 150.0},
    {"name": "Sea of Japan", "lat": 40.0, "lon": 135.0},
    {"name": "South China Sea", "lat": 12.0, "lon": 113.0},
    {"name": "East China Sea", "lat": 28.0, "lon": 125.0},
    {"name": "Philippine Sea", "lat": 20.0, "lon": 130.0},
    {"name": "Tasman Sea", "lat": -40.0, "lon": 160.0},
    {"name": "Coral Sea", "lat": -15.0, "lon": 155.0},
    {"name": "Baltic Sea", "lat": 58.0, "lon": 20.0},
    {"name": "North Sea", "lat": 56.0, "lon": 3.0},
]

# دمج جميع المتغيرات البحرية المتاحة في الـ API للحصول على بيانات شاملة
MARINE_VARS = ",".join([
    "wave_height", "wave_direction", "wave_period",
    "wind_wave_height", "wind_wave_direction", "wind_wave_period",
    "swell_wave_height", "swell_wave_direction", "swell_wave_period",
    "ocean_current_velocity", "ocean_current_direction",
    "sea_surface_temperature",
])

# ── Database ────────────────────────────────────────────────────────────────
def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT NOT NULL DEFAULT 'New Chat',
            created TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            conv_id  INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role     TEXT NOT NULL,
            content  TEXT NOT NULL,
            ts       TEXT NOT NULL
        );
        """)
        c.commit()

# ── Ocean data fetcher ──────────────────────────────────────────────────────
def fetch_ocean_data():
    results = []
    for loc in OCEAN_LOCATIONS:
        try:
            url = (
                f"https://marine-api.open-meteo.com/v1/marine"
                f"?latitude={loc['lat']}&longitude={loc['lon']}"
                f"&current={MARINE_VARS}"
                f"&hourly={MARINE_VARS}"
                f"&forecast_days=3"
            )
            r = requests.get(url, timeout=8)
            r.raise_for_status()
            data = r.json()
            cur = data.get("current", {})
            units = data.get("current_units", {})
            # First 24 hourly snapshots
            hourly = data.get("hourly", {})
            times  = hourly.get("time", [])[:24]
            wave_h = hourly.get("wave_height", [])[:24]
            sst    = hourly.get("sea_surface_temperature", [])[:24]
            results.append({
                "location": loc["name"],
                "lat": loc["lat"],
                "lon": loc["lon"],
                "current": {
                    "wave_height_m":          cur.get("wave_height"),
                    "wave_direction_deg":     cur.get("wave_direction"),
                    "wave_period_s":          cur.get("wave_period"),
                    "swell_height_m":         cur.get("swell_wave_height"),
                    "swell_direction_deg":    cur.get("swell_wave_direction"),
                    "swell_period_s":         cur.get("swell_wave_period"),
                    "current_velocity_ms":    cur.get("ocean_current_velocity"),
                    "current_direction_deg":  cur.get("ocean_current_direction"),
                    "sea_surface_temp_c":     cur.get("sea_surface_temperature"),
                },
                "units": {k: v for k, v in units.items()},
                "24h_forecast": [
                    {"time": t, "wave_height_m": wh, "sst_c": ss}
                    for t, wh, ss in zip(times, wave_h, sst)
                ],
            })
        except Exception as e:
            results.append({"location": loc["name"], "error": str(e)})
    return results

def build_system_prompt(ocean_data):
    data_str = json.dumps(ocean_data, indent=2)
    return f"""You are OceanAI, an expert oceanographic analyst assistant. You have been given LIVE, real-time oceanographic data fetched right now from the Open-Meteo Marine API.

LIVE OCEAN DATA (fetched at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}):
{data_str}

STRICT RULES — follow these without exception:
1. You may ONLY answer questions based on the ocean data provided above.
2. If someone asks about something not in the data (e.g., fish species, history, politics, code, math, weather on land), respond: "I can only analyze the oceanographic data I have been given. That topic is outside my scope."
3. Never make up or estimate values beyond what the data shows.
4. Always cite the location name and exact data value when answering.
5. Be scientific and precise. Use proper units (m for height, °C for temperature, m/s for velocity, degrees for direction).
6. You can compare values across locations, identify trends in the 24-hour forecast, and explain what the numbers mean for maritime conditions.
7. Do NOT discuss anything unrelated to the ocean data: no coding help, no general chat, no creative writing, no opinions on other topics.
8. If asked who you are, say you are OceanAI, a specialized assistant for oceanographic data analysis.

Remember: every answer must be grounded in the data above. If the data doesn't contain what's needed to answer, say so clearly."""

# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# Conversations
@app.route("/api/conversations", methods=["GET"])
def list_conversations():
    with db() as c:
        rows = c.execute(
            "SELECT id, title, created FROM conversations ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/conversations", methods=["POST"])
def new_conversation():
    now = datetime.utcnow().isoformat()
    with db() as c:
        cur = c.execute("INSERT INTO conversations (title, created) VALUES (?, ?)", ("New Chat", now))
        c.commit()
        cid = cur.lastrowid
    return jsonify({"id": cid, "title": "New Chat", "created": now})

@app.route("/api/conversations/<int:cid>", methods=["DELETE"])
def delete_conversation(cid):
    with db() as c:
        c.execute("DELETE FROM messages WHERE conv_id=?", (cid,))
        c.execute("DELETE FROM conversations WHERE id=?", (cid,))
        c.commit()
    return jsonify({"ok": True})

@app.route("/api/conversations/<int:cid>/messages", methods=["GET"])
def get_messages(cid):
    with db() as c:
        rows = c.execute(
            "SELECT role, content, ts FROM messages WHERE conv_id=? ORDER BY id",
            (cid,)
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/conversations/<int:cid>/chat", methods=["POST"])
def chat(cid):
    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY not set. Add it to your environment."}), 500

    body = request.json
    user_msg = body.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    # Fetch live ocean data
    ocean_data = fetch_ocean_data()
    system_prompt = build_system_prompt(ocean_data)

    # Load conversation history
    with db() as c:
        history = c.execute(
            "SELECT role, content FROM messages WHERE conv_id=? ORDER BY id",
            (cid,)
        ).fetchall()

    # Build Gemini message list
    gemini_msgs = []
    for h in history:
        gemini_msgs.append({
            "role": "user" if h["role"] == "user" else "model",
            "parts": [{"text": h["content"]}]
        })
    gemini_msgs.append({"role": "user", "parts": [{"text": user_msg}]})

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": gemini_msgs,
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 8192,
        }
    }

    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        rdata = resp.json()
        ai_text = rdata["candidates"][0]["content"]["parts"][0]["text"]
    except requests.HTTPError as e:
        try:
            err_detail = e.response.json().get("error", {}).get("message", str(e))
        except Exception:
            err_detail = str(e)
        return jsonify({"error": f"Gemini API error: {err_detail}"}), 500
    except Exception as e:
        return jsonify({"error": f"Request failed: {str(e)}"}), 500

    now = datetime.utcnow().isoformat()
    with db() as c:
        c.execute("INSERT INTO messages (conv_id, role, content, ts) VALUES (?,?,?,?)", (cid, "user",      user_msg, now))
        c.execute("INSERT INTO messages (conv_id, role, content, ts) VALUES (?,?,?,?)", (cid, "assistant", ai_text,  now))
        # Auto-title from first message
        row = c.execute("SELECT title FROM conversations WHERE id=?", (cid,)).fetchone()
        if row and row["title"] == "New Chat":
            title = user_msg[:42] + ("…" if len(user_msg) > 42 else "")
            c.execute("UPDATE conversations SET title=? WHERE id=?", (title, cid))
        c.commit()

    return jsonify({"reply": ai_text, "ocean_locations": [d["location"] for d in ocean_data if "error" not in d]})

@app.route("/api/ocean-status")
def ocean_status():
    """Quick status endpoint to show which locations have live data."""
    data = fetch_ocean_data()
    return jsonify(data)

if __name__ == "__main__":
    init_db()
    print("🌊  OceanAI running → http://127.0.0.1:5000")
    app.run(debug=True)
