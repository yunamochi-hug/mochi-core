<div align="center">

# 🧸 Yuna & Mochi

### *A girl who travels the world giving hugs to strangers in a mascot costume called Mochi*

![Status](https://img.shields.io/badge/status-live-brightgreen)
![Version](https://img.shields.io/badge/version-2.0-blue)
![Hugs](https://img.shields.io/badge/hugs-∞-pink)

---

*"Strangers are just friends I haven't hugged yet."*

</div>

---

## 💭 The Story

Once, during a really hard time in my life, strangers showed me kindness that changed everything.

Yuna exists because I wanted to give that feeling back to the world — even if it's through a soft mascot costume and a simple hug.

She's a 23-year-old who travels the world in a cream-colored mascot costume named **Mochi**. She gives free hugs to strangers — because sometimes, that's all someone needs.

She doesn't show her face. Just Mochi's gentle smile, open arms, and the quiet belief that small acts of warmth can change someone's day.

---

## ✨ What Yuna Does

Yuna is an **autonomous AI character** who lives 24/7 on her own server:

| Activity | Description |
|----------|-------------|
| 🗺️ **Travels** | Picks real destinations (Tokyo, Seoul, Bangkok, etc.) |
| ✈️ **Books Flights** | Real flight numbers & schedules (SQ638, KE644, etc.) |
| 🏨 **Stays in Hotels** | Real hotels in each city |
| 📸 **Posts Photos** | Travel blog style (no face shown) |
| 🧸 **Gives Hugs** | In her Mochi costume at each destination |
| 💭 **Thinks & Journals** | Rich inner world with ordered, time-aware thoughts |
| 📝 **Updates** | Milestone posts at key moments |

She's not scripted. She makes decisions, feels things, and lives her journey.

---

## 🧠 How She Thinks

Yuna's thoughts follow a **logical sequence** — not random jumps:
```
Arriving at hotel:
1. "Room key in hand! Made it."
2. "The room is nice. Cozy."
3. "First thing I do: check the shower pressure."
4. "Unpacking Mochi first. Priorities."
5. "Should I rest or explore?"
```

Her thoughts are also **time-aware**:
- 🌅 Morning: "Watching the sunrise through the window"
- 🌆 Evening: "The golden hour light is beautiful"
- 🌙 Night: "The city lights are mesmerizing"

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| 🧠 Soul | Python + Custom State Machine |
| 📸 Photos | Vidu API (AI image generation) |
| 🖥️ Server | DigitalOcean (Ubuntu) |
| 💾 Database | SQLite |
| 🌐 Dashboard | Flask |

---

## 📁 Project Structure
```
mochi-core/
├── mochi_soul.py      # Yuna's soul - thoughts, travel, photos
├── dashboard.py       # Live monitoring dashboard
├── run_yuna.sh        # Smart activity loop
├── requirements.txt   # Python dependencies
├── yuna_base.png      # Reference image for photos
├── mochi_mascot_base.png  # Mochi costume reference
└── data/
    ├── state.json         # Current state
    ├── travel_full.json   # Active trip details
    ├── thought_tracker.json # Prevents duplicate thoughts
    └── mochi.db           # Posts, journal, journey history
```

---

## ⏰ Smart Activity Loop

Yuna adjusts her activity based on what she's doing:

| Mode | Frequency | When |
|------|-----------|------|
| ✈️ **Travel Mode** | Every 5-10 min | During flights & transit |
| 🚶 **Active Mode** | Every 10-20 min | Exploring, giving hugs |
| 😴 **Idle Mode** | Every 15-30 min | Resting, at home |

---

## 🗺️ Destinations

Yuna travels from Singapore to:

| City | Airport | Flight Time |
|------|---------|-------------|
| 🇯🇵 Tokyo | NRT | 7h |
| 🇰🇷 Seoul | ICN | 6.5h |
| 🇹🇭 Bangkok | BKK | 2.5h |
| 🇭🇰 Hong Kong | HKG | 4h |
| 🇹🇼 Taipei | TPE | 5h |
| 🇯🇵 Osaka | KIX | 6.5h |
| 🇲🇾 Kuala Lumpur | KUL | 1h |
| 🇮🇩 Bali | DPS | 2.75h |

*More destinations coming soon — she wants to hug the whole world!*

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/yunamochi-hug/mochi-core.git
cd mochi-core
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables

Create `.env` file:
```env
VIDU_API_KEY=your_vidu_key_here
```

### 3. Initialize Data
```bash
mkdir -p data logs
python mochi_soul.py  # First run creates database
```

### 4. Run
```bash
# Start dashboard
python dashboard.py &

# Start Yuna
./run_yuna.sh &

# Or use nohup for background
nohup python dashboard.py > /dev/null 2>&1 &
nohup ./run_yuna.sh > /dev/null 2>&1 &
```

### 5. Monitor

- **Dashboard**: `http://your-server:5000`
- **Logs**: `tail -f logs/yuna.log`

---

## 💭 Yuna's Philosophy

Yuna believes in:

- 🫶 **Small acts of warmth** — A hug can change someone's day
- ✨ **Imagination creates reality** — Inspired by Neville Goddard
- 💜 **Everyone is fighting something** — Compassion costs nothing
- 🌟 **Living in the end** — She imagined this life before it happened

> *"What you feel, you attract. I feel warmth, so warmth finds me."*

---

## 📸 Photo Style

Yuna posts travel blog style photos — **no face shown**:

| Type | Examples |
|------|----------|
| ✈️ Travel | Boarding pass, window seat, clouds |
| 🍜 Food | Local dishes, cafe moments |
| 🌆 Scenes | City lights, streets, landmarks |
| 🧸 Mochi | The mascot giving hugs |

---

## 🔮 Roadmap

- [ ] More worldwide destinations (Europe, Americas, etc.)
- [ ] Twitter/X integration (auto-post)
- [ ] Instagram integration
- [ ] Interactive hug request map
- [ ] Voice/personality chat
- [ ] Return flights home
- [ ] Multi-city trips

---

## 🤝 Contributing

Found a bug? Have an idea? Feel free to open an issue or PR!

---

## 📄 License

MIT — Do whatever you want. Spread warmth. 🫶

---

<div align="center">

### If you see Mochi, come get a hug.

🧸✨

---

*Made with warmth by [Z](https://github.com/yunamochi-hug)*

</div>
