"""
YUNA Dashboard v2 - Fixed version
"""

from flask import Flask, render_template_string, jsonify
import sqlite3
import json
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🫶 Yuna</title>
    <meta http-equiv="refresh" content="30">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #eee; min-height: 100vh; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 30px; font-size: 2.5em; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
        .card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 24px; border: 1px solid rgba(255,255,255,0.1); }
        .card h2 { font-size: 1.1em; color: #888; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 1px; }
        .card.travel-card { background: linear-gradient(135deg, rgba(255,107,107,0.15) 0%, rgba(78,205,196,0.15) 100%); border: 1px solid rgba(255,107,107,0.3); grid-column: span 2; }
        @media (max-width: 800px) { .card.travel-card { grid-column: span 1; } }
        .status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .status-item { background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; }
        .status-item .label { font-size: 0.8em; color: #666; margin-bottom: 4px; }
        .status-item .value { font-size: 1.2em; color: #fff; }
        .energy-bar { width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; margin-top: 8px; }
        .energy-fill { height: 100%; background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb); border-radius: 4px; }
        .thought-box { font-size: 1.1em; line-height: 1.6; color: #ddd; font-style: italic; padding: 16px; background: rgba(255,255,255,0.03); border-radius: 8px; border-left: 3px solid #feca57; }
        .boarding-pass { background: linear-gradient(135deg, #fff 0%, #f0f0f0 100%); color: #333; border-radius: 12px; padding: 20px; }
        .boarding-pass .airline { font-size: 0.9em; color: #666; }
        .boarding-pass .flight-number { font-size: 2em; font-weight: bold; color: #e74c3c; }
        .boarding-pass .route { display: flex; justify-content: space-between; align-items: center; margin: 15px 0; padding: 15px 0; border-top: 1px dashed #ccc; border-bottom: 1px dashed #ccc; }
        .boarding-pass .city { text-align: center; }
        .boarding-pass .city-code { font-size: 1.8em; font-weight: bold; color: #333; }
        .boarding-pass .city-name { font-size: 0.8em; color: #666; }
        .boarding-pass .city-time { font-size: 0.9em; color: #e74c3c; margin-top: 5px; }
        .boarding-pass .plane-icon { font-size: 1.5em; color: #3498db; }
        .boarding-pass .details { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 10px; }
        .boarding-pass .detail-item { text-align: center; }
        .boarding-pass .detail-label { font-size: 0.7em; color: #999; text-transform: uppercase; }
        .boarding-pass .detail-value { font-size: 1em; font-weight: bold; color: #333; }
        .hotel-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 20px; margin-top: 15px; }
        .hotel-card .hotel-name { font-size: 1.3em; font-weight: bold; color: #fff; }
        .hotel-card .hotel-area { color: rgba(255,255,255,0.8); margin-top: 5px; }
        .hotel-card .hotel-price { margin-top: 10px; font-size: 1.1em; color: #feca57; }
        .timeline { margin-top: 20px; position: relative; padding-left: 30px; max-height: 350px; overflow-y: auto; }
        .timeline::before { content: ''; position: absolute; left: 10px; top: 0; bottom: 0; width: 2px; background: rgba(255,255,255,0.2); }
        .timeline-item { position: relative; padding: 8px 0; padding-left: 20px; }
        .timeline-item::before { content: ''; position: absolute; left: -24px; top: 12px; width: 10px; height: 10px; border-radius: 50%; background: #48dbfb; border: 2px solid #16213e; }
        .timeline-item.completed::before { background: #00b894; }
        .timeline-item.current::before { background: #feca57; box-shadow: 0 0 10px #feca57; animation: pulse 1s infinite; }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.3); } }
        .timeline-item .time { font-size: 0.8em; color: #48dbfb; font-weight: bold; }
        .timeline-item .step-name { font-size: 0.75em; color: #888; text-transform: uppercase; }
        .timeline-item .description { color: #ddd; font-size: 0.9em; }
        .post-item { padding: 16px; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 12px; }
        .post-media { margin: 12px 0; border-radius: 8px; overflow: hidden; }
        .post-media img { width: 100%; max-height: 250px; object-fit: cover; }
        .post-caption { color: #ddd; line-height: 1.5; }
        .post-meta { font-size: 0.8em; color: #666; margin-top: 8px; }
        .journal-entry { padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 10px; font-size: 0.95em; }
        .journal-meta { font-size: 0.75em; color: #666; margin-top: 6px; }
        .journey-item { padding: 10px; border-left: 2px solid #48dbfb; margin-bottom: 10px; margin-left: 10px; }
        .refresh-note { text-align: center; color: #555; font-size: 0.8em; margin-top: 30px; }
        .mochi-banner { background: linear-gradient(90deg, #ffecd2 0%, #fcb69f 100%); color: #333; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
        .mochi-banner .emoji { font-size: 2em; }
        .hugs-counter { font-size: 1.8em; font-weight: bold; color: #e74c3c; }
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; }
        .status-badge.traveling { background: #3498db; color: white; }
        .status-badge.exploring { background: #2ecc71; color: white; }
        .status-badge.resting { background: #9b59b6; color: white; }
        .status-badge.hugging { background: #e74c3c; color: white; }
        .completed-banner { background: linear-gradient(90deg, #00b894 0%, #00cec9 100%); color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🫶 Yuna</h1>
        
        {% if state.current_step == 'mochi_time' %}
        <div class="mochi-banner">
            <div class="emoji">🧸</div>
            <div>Mochi is giving hugs in {{ state.location }}!</div>
            {% if state.mochi_hugs_today > 0 %}<div class="hugs-counter">{{ state.mochi_hugs_today }} hugs today!</div>{% endif %}
        </div>
        {% endif %}
        
        <div class="grid">
            <div class="card">
                <h2>📍 Status</h2>
                <div class="status-grid">
                    <div class="status-item">
                        <div class="label">Location</div>
                        <div class="value">{{ state.display_location or state.location }}</div>
                    </div>
                    <div class="status-item">
                        <div class="label">Status</div>
                        <div class="value">
                            {% if 'flight' in state.current_step.lower() or state.current_step in ['boarding', 'landed'] %}
                            <span class="status-badge traveling">✈️ {{ state.current_step_display }}</span>
                            {% elif state.current_step == 'mochi_time' %}
                            <span class="status-badge hugging">🧸 Giving Hugs</span>
                            {% elif state.current_step == 'exploring' %}
                            <span class="status-badge exploring">🚶 Exploring</span>
                            {% elif state.current_step in ['resting', 'night'] %}
                            <span class="status-badge resting">😴 Resting</span>
                            {% else %}
                            {{ state.current_step_display }}
                            {% endif %}
                        </div>
                    </div>
                    <div class="status-item">
                        <div class="label">Local Time</div>
                        <div class="value">{{ state.local_time }}</div>
                    </div>
                    <div class="status-item">
                        <div class="label">Mood</div>
                        <div class="value">{{ state.mood }}</div>
                    </div>
                    <div class="status-item">
                        <div class="label">Energy</div>
                        <div class="value">{{ state.energy }}%</div>
                        <div class="energy-bar"><div class="energy-fill" style="width: {{ state.energy }}%"></div></div>
                    </div>
                    <div class="status-item">
                        <div class="label">Day</div>
                        <div class="value">Day {{ state.days_in_location }} in {{ state.location }}</div>
                    </div>
                </div>
                {% if state.home_base %}<div class="status-item" style="margin-top: 12px;"><div class="label">🏨 Staying At</div><div class="value" style="font-size: 1em;">{{ state.home_base }}</div></div>{% endif %}
            </div>
            
            <div class="card">
                <h2>💭 Latest Thought</h2>
                {% if latest_thought %}
                <div class="thought-box">"{{ latest_thought.entry }}"</div>
                <div class="post-meta">{{ latest_thought.location }} · {{ latest_thought.time_ago }}</div>
                {% else %}
                <p style="color: #666;">No thoughts yet...</p>
                {% endif %}
            </div>
            
            {% if travel.flight and travel.status != 'idle' %}
            <div class="card travel-card">
                <h2>✈️ Travel Itinerary</h2>
                
                {% if travel.status == 'completed' %}
                <div class="completed-banner">
                    ✅ Arrived in {{ travel.current_trip.to }}!
                </div>
                {% endif %}
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                    <div>
                        <div class="boarding-pass">
                            <div class="airline">{{ travel.flight.airline }}</div>
                            <div class="flight-number">{{ travel.flight.flight }}</div>
                            <div class="route">
                                <div class="city">
                                    <div class="city-code">SIN</div>
                                    <div class="city-name">{{ travel.flight.from_city }}</div>
                                    <div class="city-time">{{ travel.flight.departure_display }}</div>
                                </div>
                                <div class="plane-icon">✈️</div>
                                <div class="city">
                                    <div class="city-code">{{ travel.flight.to_code or travel.flight.to_city[:3] | upper }}</div>
                                    <div class="city-name">{{ travel.flight.to_city }}</div>
                                    <div class="city-time">{{ travel.flight.arrival_display }}</div>
                                </div>
                            </div>
                            <div class="details">
                                <div class="detail-item"><div class="detail-label">Terminal</div><div class="detail-value">{{ travel.flight.dep_terminal }}</div></div>
                                <div class="detail-item"><div class="detail-label">Gate</div><div class="detail-value">{{ travel.flight.gate or 'TBA' }}</div></div>
                                <div class="detail-item"><div class="detail-label">Seat</div><div class="detail-value">{{ travel.flight.seat or 'TBA' }}</div></div>
                                <div class="detail-item"><div class="detail-label">Duration</div><div class="detail-value">{{ travel.flight.duration }}h</div></div>
                            </div>
                        </div>
                        {% if travel.hotel %}
                        <div class="hotel-card">
                            <div class="hotel-name">🏨 {{ travel.hotel.name }}</div>
                            <div class="hotel-area">{{ travel.hotel.area }}, {{ travel.hotel.city }}</div>
                            <div class="hotel-price">${{ travel.hotel.price_per_night }}/night</div>
                        </div>
                        {% endif %}
                    </div>
                    <div>
                        <h3 style="color: #888; margin-bottom: 10px;">📅 Timeline</h3>
                        <div class="timeline">
                            {% for step in travel.timeline %}
                            <div class="timeline-item {% if loop.index0 < travel.current_step_index %}completed{% endif %} {% if loop.index0 == travel.current_step_index %}current{% endif %}">
                                <div class="time">{{ step.display_time }}</div>
                                <div class="step-name">{{ step.step | replace('_', ' ') }}</div>
                                <div class="description">{{ step.description }}</div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                {% if travel.current_trip and travel.current_trip.reason %}
                <div style="margin-top: 15px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px; color: #aaa;">
                    📝 {{ travel.current_trip.reason }}
                </div>
                {% endif %}
            </div>
            {% endif %}
            
            <div class="card">
                <h2>📸 Recent Posts</h2>
                {% if posts %}
                {% for post in posts[:5] %}
                <div class="post-item">
                    {% if post.content_url %}
                    <div class="post-media"><img src="{{ post.content_url }}" onerror="this.style.display='none'"></div>
                    {% endif %}
                    {% if post.caption %}
                    <div class="post-caption">"{{ post.caption }}"</div>
                    {% endif %}
                    <div class="post-meta">📍 {{ post.location }} · {{ post.time_ago }}</div>
                </div>
                {% endfor %}
                {% else %}
                <p style="color: #666;">No posts yet...</p>
                {% endif %}
            </div>
            
            <div class="card">
                <h2>📓 Journal</h2>
                {% if journal_entries %}
                {% for entry in journal_entries[:8] %}
                <div class="journal-entry">
                    {{ entry.entry[:120] }}{% if entry.entry|length > 120 %}...{% endif %}
                    <div class="journal-meta">{{ entry.mood }} · 📍 {{ entry.location }} · {{ entry.time_ago }}</div>
                </div>
                {% endfor %}
                {% else %}
                <p style="color: #666;">No entries yet...</p>
                {% endif %}
            </div>
            
            <div class="card">
                <h2>🗺️ Journey</h2>
                {% if journey %}
                {% for stop in journey[:8] %}
                <div class="journey-item">
                    <strong>{{ stop.location }}</strong>
                    {% if stop.notes %}<div style="font-size: 0.85em; color: #aaa;">{{ stop.notes }}</div>{% endif %}
                    <div class="journal-meta">{{ stop.time_ago }}</div>
                </div>
                {% endfor %}
                {% else %}
                <p style="color: #666;">Journey starting...</p>
                {% endif %}
            </div>
        </div>
        
        <p class="refresh-note">Auto-refreshes every 30s · {{ now }}</p>
    </div>
</body>
</html>
"""

def get_db():
    return sqlite3.connect("data/mochi.db")

def time_ago(dt_str):
    if not dt_str:
        return "unknown"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            now = datetime.now()
        else:
            now = datetime.now(dt.tzinfo)
        diff = now - dt
        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        mins = diff.seconds // 60
        if mins > 0:
            return f"{mins}m ago"
        return "just now"
    except:
        return "unknown"

def format_step(step):
    """Convert step_name to readable: checked_in_hotel -> Checked In Hotel"""
    if not step:
        return "Idle"
    return step.replace("_", " ").title()

def get_state():
    try:
        with open("data/state.json", "r") as f:
            state = json.load(f)
    except:
        state = {}
    
    tz = ZoneInfo(state.get("timezone", "Asia/Singapore"))
    local_time = datetime.now(tz)
    home = state.get("home_base", {})
    current_step = state.get("current_step", state.get("travel_state", "idle"))
    
    return {
        "location": state.get("location", "Singapore"),
        "display_location": state.get("display_location", state.get("location", "Singapore")),
        "energy": state.get("energy", 80),
        "mood": state.get("mood", "peaceful"),
        "days_in_location": state.get("days_in_location", 1),
        "local_time": local_time.strftime("%I:%M %p"),
        "home_base": home.get("name", "") if home else "",
        "current_step": current_step,
        "current_step_display": format_step(current_step),
        "mochi_hugs_today": state.get("mochi_hugs_today", 0),
    }

def get_travel():
    try:
        with open("data/travel_full.json", "r") as f:
            return json.load(f)
    except:
        return {}

def get_posts():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT content_type, content_url, caption, location, created_at, shared FROM posts ORDER BY created_at DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        return [{"content_type": r[0], "content_url": r[1], "caption": r[2], "location": r[3], "shared": r[5], "time_ago": time_ago(r[4])} for r in rows]
    except:
        return []

def get_journal():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT entry, mood, location, created_at FROM journal ORDER BY created_at DESC LIMIT 15")
        rows = c.fetchall()
        conn.close()
        return [{"entry": r[0], "mood": r[1], "location": r[2], "time_ago": time_ago(r[3])} for r in rows]
    except:
        return []

def get_journey():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT location, arrived_at, notes FROM journey ORDER BY arrived_at DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        return [{"location": r[0], "notes": r[2], "time_ago": time_ago(r[1])} for r in rows]
    except:
        return []

@app.route('/')
def dashboard():
    state = get_state()
    travel = get_travel()
    posts = get_posts()
    journal = get_journal()
    journey = get_journey()
    latest_thought = journal[0] if journal else None
    return render_template_string(
        DASHBOARD_HTML,
        state=state,
        travel=travel,
        posts=posts,
        journal_entries=journal,
        journey=journey,
        latest_thought=latest_thought,
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/api/status')
def api_status():
    return jsonify({"state": get_state(), "travel": get_travel()})

if __name__ == "__main__":
    print("🫶 Yuna Dashboard v2: http://152.42.177.43:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
