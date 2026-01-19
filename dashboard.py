"""
YUNA Dashboard - A simple web interface to monitor Yuna's life
"""

from flask import Flask, render_template_string, jsonify, send_from_directory
import sqlite3
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

# Dashboard HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🫶 Yuna - Live Dashboard</title>
    <meta http-equiv="refresh" content="60">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { 
            text-align: center; 
            margin-bottom: 30px; 
            font-size: 2.5em;
            color: #fff;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 {
            font-size: 1.1em;
            color: #888;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        .status-item {
            background: rgba(255,255,255,0.03);
            padding: 12px;
            border-radius: 8px;
        }
        .status-item .label {
            font-size: 0.8em;
            color: #666;
            margin-bottom: 4px;
        }
        .status-item .value {
            font-size: 1.2em;
            color: #fff;
        }
        .energy-bar {
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            margin-top: 8px;
            overflow: hidden;
        }
        .energy-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb);
            border-radius: 4px;
            transition: width 0.3s;
        }
        .thought-box {
            font-size: 1.1em;
            line-height: 1.6;
            color: #ddd;
            font-style: italic;
            padding: 16px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            border-left: 3px solid #feca57;
        }
        .post-item {
            padding: 16px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            margin-bottom: 12px;
        }
        .post-item:last-child { margin-bottom: 0; }
        .post-type {
            font-size: 0.75em;
            padding: 4px 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            display: inline-block;
            margin-bottom: 8px;
        }
        .post-caption {
            color: #ddd;
            line-height: 1.5;
        }
        .post-meta {
            font-size: 0.8em;
            color: #666;
            margin-top: 8px;
        }
        .post-media {
            margin: 12px 0;
            border-radius: 8px;
            overflow: hidden;
        }
        .post-media img, .post-media video {
            width: 100%;
            max-height: 300px;
            object-fit: cover;
        }
        .journal-entry {
            padding: 12px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 0.95em;
            line-height: 1.5;
        }
        .journal-entry:last-child { margin-bottom: 0; }
        .journal-meta {
            font-size: 0.75em;
            color: #666;
            margin-top: 6px;
        }
        .journey-item {
            padding: 10px;
            border-left: 2px solid #48dbfb;
            margin-bottom: 10px;
            margin-left: 10px;
        }
        .mood-peaceful { color: #48dbfb; }
        .mood-contemplative { color: #a29bfe; }
        .mood-energetic { color: #feca57; }
        .mood-melancholic { color: #ff6b6b; }
        .mood-curious { color: #26de81; }
        .refresh-note {
            text-align: center;
            color: #555;
            font-size: 0.8em;
            margin-top: 30px;
        }
        .time-ago {
            color: #48dbfb;
        }
        .sleeping-banner {
            background: linear-gradient(90deg, #2d3436, #636e72);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
        }
        .sleeping-banner .emoji { font-size: 3em; }
        .awake-banner {
            background: linear-gradient(90deg, #00b894, #00cec9);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🫶 Yuna</h1>
        
        {% if state.should_be_asleep %}
        <div class="sleeping-banner">
            <div class="emoji">😴</div>
            <p>Yuna is sleeping... ({{ state.body_time }})</p>
        </div>
        {% endif %}
        
        <div class="grid">
            <!-- Status Card -->
            <div class="card">
                <h2>📍 Current Status</h2>
                <div class="status-grid">
                    <div class="status-item">
                        <div class="label">Location</div>
                        <div class="value">{{ state.location }}</div>
                    </div>
                    <div class="status-item">
                        <div class="label">Day</div>
                        <div class="value">Day {{ state.days_in_location }}</div>
                    </div>
                    <div class="status-item">
                        <div class="label">Local Time</div>
                        <div class="value">{{ state.local_time }}</div>
                    </div>
                    <div class="status-item">
                        <div class="label">Time of Day</div>
                        <div class="value">{{ state.time_of_day }}</div>
                    </div>
                    <div class="status-item">
                        <div class="label">Mood</div>
                        <div class="value mood-{{ state.mood }}">{{ state.mood }}</div>
                    </div>
                    <div class="status-item">
                        <div class="label">Jet Lag</div>
                        <div class="value">{{ "Day " ~ state.jet_lag_days if state.jet_lag_days > 0 else "None ✓" }}</div>
                    </div>
                </div>
                <div class="status-item" style="margin-top: 12px;">
                    <div class="label">Energy</div>
                    <div class="value">{{ state.energy }}%</div>
                    <div class="energy-bar">
                        <div class="energy-fill" style="width: {{ state.energy }}%"></div>
                    </div>
                </div>
            </div>
            
            <!-- Latest Thought Card -->
            <div class="card">
                <h2>💭 Latest Thought</h2>
                {% if latest_thought %}
                <div class="thought-box">
                    "{{ latest_thought.entry }}"
                </div>
                <div class="post-meta">{{ latest_thought.time_ago }}</div>
                {% else %}
                <p style="color: #666;">No thoughts yet...</p>
                {% endif %}
            </div>
            
            <!-- Recent Posts Card -->
            <div class="card">
                <h2>📸 Recent Posts</h2>
                {% if posts %}
                    {% for post in posts[:5] %}
                    <div class="post-item">
                        <span class="post-type">
                            {% if post.content_type == 'video' %}🎬 Video
                            {% elif post.content_type == 'image' %}📸 Photo
                            {% else %}💭 Thought
                            {% endif %}
                        </span>
                        {% if post.shared %}<span class="post-type" style="background: #00b894;">Shared</span>{% endif %}
                        
                        {% if post.content_url and post.content_type == 'image' %}
                        <div class="post-media">
                            <img src="{{ post.content_url }}" alt="Post image" onerror="this.style.display='none'">
                        </div>
                        {% elif post.content_url and post.content_type == 'video' %}
                        <div class="post-media">
                            <video controls muted>
                                <source src="{{ post.content_url }}" type="video/mp4">
                            </video>
                        </div>
                        {% endif %}
                        
                        {% if post.caption %}
                        <div class="post-caption">"{{ post.caption }}"</div>
                        {% endif %}
                        <div class="post-meta">{{ post.location }} · {{ post.time_ago }}</div>
                    </div>
                    {% endfor %}
                {% else %}
                <p style="color: #666;">No posts yet...</p>
                {% endif %}
            </div>
            
            <!-- Journal Card -->
            <div class="card">
                <h2>📓 Private Journal</h2>
                {% if journal_entries %}
                    {% for entry in journal_entries[:5] %}
                    <div class="journal-entry">
                        {{ entry.entry[:200] }}{% if entry.entry|length > 200 %}...{% endif %}
                        <div class="journal-meta">{{ entry.mood }} · {{ entry.location }} · {{ entry.time_ago }}</div>
                    </div>
                    {% endfor %}
                {% else %}
                <p style="color: #666;">No journal entries yet...</p>
                {% endif %}
            </div>
            
            <!-- Journey Card -->
            <div class="card">
                <h2>✈️ Journey Log</h2>
                {% if journey %}
                    {% for stop in journey[:10] %}
                    <div class="journey-item">
                        <strong>{{ stop.location }}</strong>
                        <div class="journal-meta">{{ stop.time_ago }}</div>
                    </div>
                    {% endfor %}
                {% else %}
                <p style="color: #666;">Journey just started...</p>
                {% endif %}
            </div>
        </div>
        
        <p class="refresh-note">Auto-refreshes every 60 seconds · Last updated: {{ now }}</p>
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
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "just now"
    except:
        return "unknown"

def get_state():
    try:
        with open("data/state.json", "r") as f:
            state = json.load(f)
    except:
        state = {
            "location": "Singapore",
            "timezone": "Asia/Singapore",
            "energy": 70,
            "mood": "peaceful",
            "jet_lag_days": 0,
            "days_in_location": 1
        }
    
    # Calculate times
    tz = ZoneInfo(state.get("timezone", "Asia/Singapore"))
    local_time = datetime.now(tz)
    
    hour = local_time.hour
    if 5 <= hour < 9:
        time_of_day = "early morning 🌅"
    elif 9 <= hour < 12:
        time_of_day = "morning ☀️"
    elif 12 <= hour < 14:
        time_of_day = "midday 🌞"
    elif 14 <= hour < 17:
        time_of_day = "afternoon 🌤️"
    elif 17 <= hour < 20:
        time_of_day = "evening 🌆"
    elif 20 <= hour < 23:
        time_of_day = "night 🌙"
    else:
        time_of_day = "late night 🌃"
    
    body_tz = ZoneInfo(state.get("body_clock_tz", state.get("timezone", "Asia/Singapore")))
    body_time = datetime.now(body_tz)
    body_hour = body_time.hour
    should_be_asleep = 23 <= body_hour or body_hour < 7
    
    return {
        "location": state.get("location", "Singapore"),
        "energy": state.get("energy", 70),
        "mood": state.get("mood", "peaceful"),
        "jet_lag_days": state.get("jet_lag_days", 0),
        "days_in_location": state.get("days_in_location", 1),
        "local_time": local_time.strftime("%I:%M %p"),
        "time_of_day": time_of_day,
        "body_time": body_time.strftime("%I:%M %p"),
        "should_be_asleep": should_be_asleep
    }

def get_posts():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT content_type, content_url, caption, location, created_at, shared FROM posts ORDER BY created_at DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        
        return [{
            "content_type": r[0],
            "content_url": r[1],
            "caption": r[2],
            "location": r[3],
            "created_at": r[4],
            "shared": r[5],
            "time_ago": time_ago(r[4])
        } for r in rows]
    except:
        return []

def get_journal():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT entry, mood, location, created_at FROM journal ORDER BY created_at DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        
        return [{
            "entry": r[0],
            "mood": r[1],
            "location": r[2],
            "created_at": r[3],
            "time_ago": time_ago(r[3])
        } for r in rows]
    except:
        return []

def get_journey():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT location, arrived_at, notes FROM journey ORDER BY arrived_at DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        
        return [{
            "location": r[0],
            "arrived_at": r[1],
            "notes": r[2],
            "time_ago": time_ago(r[1])
        } for r in rows]
    except:
        return []

@app.route('/')
def dashboard():
    state = get_state()
    posts = get_posts()
    journal_entries = get_journal()
    journey = get_journey()
    
    # Get latest thought from journal
    latest_thought = journal_entries[0] if journal_entries else None
    
    return render_template_string(
        DASHBOARD_HTML,
        state=state,
        posts=posts,
        journal_entries=journal_entries,
        journey=journey,
        latest_thought=latest_thought,
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/api/status')
def api_status():
    return jsonify(get_state())

@app.route('/api/posts')
def api_posts():
    return jsonify(get_posts())

@app.route('/api/journal')
def api_journal():
    return jsonify(get_journal())

if __name__ == "__main__":
    print("🫶 Yuna Dashboard starting...")
    print("📍 Open http://152.42.177.43:5000 in your browser")
    app.run(host='0.0.0.0', port=5000, debug=False)
