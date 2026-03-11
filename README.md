# 🌊 OceanAI — Real-Time Oceanographic Chat Assistant

OceanAI is a Flask-based web application that provides a conversational interface for analyzing **live oceanographic data**. Powered by Google Gemini and the Open-Meteo Marine API, it lets users query real-time conditions — wave heights, sea surface temperatures, ocean currents, and more — across 25+ major oceans and seas worldwide.

---

## ✨ Features

- **Live Marine Data** — Fetches real-time data from the [Open-Meteo Marine API](https://open-meteo.com/en/docs/marine-weather-api) on every chat request
- **AI-Powered Analysis** — Uses Google Gemini (`gemini-3-flash-preview`) to interpret and explain oceanographic conditions
- **Multi-Conversation Support** — Create, switch between, and delete multiple chat sessions
- **Persistent Chat History** — Conversations and messages are stored in a local SQLite database
- **25+ Global Locations** — Covers all major oceans, seas, and gulfs (Pacific, Atlantic, Indian, Red Sea, Arabian Gulf, Mediterranean, and more)
- **24-Hour Forecasts** — Includes hourly wave height and sea surface temperature forecasts for the next 24 hours
- **Strict Scope Enforcement** — The AI only answers questions grounded in the provided ocean data

---

## 🗂️ Project Structure

```
.
├── app.py              # Flask backend — API routes, data fetcher, Gemini integration
├── templates/
│   └── index.html      # Frontend UI
├── ocean_chat.db       # SQLite database (auto-created on first run)
├── .env                # Environment variables (not committed)
└── requirements.txt    # Python dependencies
```

---

## 🌐 Data Coverage

The app monitors the following locations:

| Category         | Locations |
|------------------|-----------|
| **Oceans**       | North/South Pacific, North/South Atlantic, Indian, Arctic, Southern |
| **Middle East**  | Red Sea, Arabian Gulf, Arabian Sea, Mediterranean, Black Sea, Caspian Sea |
| **Americas**     | Caribbean Sea, Gulf of Mexico |
| **Asia-Pacific** | Bering Sea, Sea of Okhotsk, Sea of Japan, South/East China Sea, Philippine Sea, Tasman Sea, Coral Sea |
| **Europe**       | Baltic Sea, North Sea |

---

## 📊 Marine Variables Tracked

| Variable | Description |
|---|---|
| `wave_height` | Significant wave height (m) |
| `wave_direction` | Wave direction (°) |
| `wave_period` | Wave period (s) |
| `wind_wave_height/direction/period` | Wind-driven wave metrics |
| `swell_wave_height/direction/period` | Swell metrics |
| `ocean_current_velocity` | Current speed (m/s) |
| `ocean_current_direction` | Current direction (°) |
| `sea_surface_temperature` | SST (°C) |

---

## ⚙️ Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/sami200511/AI-Oceanographic-Analyzer.git
cd AI-Oceanographic-Analyzer
```

### 2. Install dependencies

```bash
pip install flask python-dotenv requests
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

> Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 4. Run the application

```bash
python app.py
```

The app will be available at **http://127.0.0.1:5000**

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the frontend UI |
| `GET` | `/api/conversations` | List all conversations |
| `POST` | `/api/conversations` | Create a new conversation |
| `DELETE` | `/api/conversations/<id>` | Delete a conversation |
| `GET` | `/api/conversations/<id>/messages` | Get message history for a conversation |
| `POST` | `/api/conversations/<id>/chat` | Send a message and receive an AI reply |
| `GET` | `/api/ocean-status` | Get live status of all monitored ocean locations |

---

## 💬 Example Queries

- *"What are the current wave heights in the Arabian Gulf?"*
- *"Which ocean has the highest sea surface temperature right now?"*
- *"Compare wave conditions between the North Atlantic and the Mediterranean."*
- *"What is the 24-hour wave forecast for the Red Sea?"*
- *"Are ocean currents strong in the Bering Sea today?"*

---

## 🤖 AI Behavior

OceanAI is configured with strict rules:

- **Only answers from live data** — no hallucinated values
- **Cites exact location names and data values** in every response
- **Out-of-scope questions** (coding, history, general chat) are declined with a clear message
- **Scientific precision** — uses proper units throughout (m, °C, m/s, °)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Flask |
| AI Model | Google Gemini (`gemini-3-flash-preview`) |
| Marine Data | Open-Meteo Marine API |
| Database | SQLite |
| Frontend | HTML/CSS/JS (served via Flask templates) |
