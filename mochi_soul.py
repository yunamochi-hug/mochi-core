"""
YUNA - A girl who travels the world giving hugs in a mascot costume called Mochi.

Features:
- Life continuity (no teleporting)
- Wardrobe changes (different clothes each day)
- Memory of her entire life
- Home base / hotel (must go home to sleep)
- Daily routine (morning → day → evening → home → sleep)
- Travel system (plan trips, book flights/hotels)
"""

import anthropic
import requests
import os
import time
import json
import sqlite3
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from travel import TravelPlanner

load_dotenv()


# ==================== APPEARANCE SYSTEM ====================

class YunaAppearance:
    def __init__(self, state_file="data/appearance.json"):
        self.state_file = state_file
        
        self.tops = [
            "white t-shirt",
            "black tank top", 
            "oversized beige sweater",
            "light blue denim jacket over white top",
            "simple grey hoodie",
            "black t-shirt",
            "cream linen shirt",
            "soft pink cardigan over white camisole",
            "vintage graphic t-shirt",
            "navy blue blouse"
        ]
        
        self.bottoms = [
            "blue jeans",
            "black shorts",
            "flowy midi skirt",
            "comfortable joggers",
            "denim shorts",
            "black leggings",
            "khaki pants",
            "white linen pants"
        ]
        
        self.dresses = [
            "simple floral sundress",
            "casual white linen dress",
            "soft blue cotton dress",
            "black casual dress"
        ]
        
        self.hair_styles = [
            "short black messy hair",
            "short black hair with small clip",
            "short black hair tucked behind ears",
            "short black hair slightly windswept",
            "short black hair under a cap"
        ]
        
        self.accessories = [
            "small canvas backpack",
            "worn tote bag",
            "no bag just phone in back pocket",
            "crossbody bag",
            "small leather satchel"
        ]
        
        self.load_today()
    
    def load_today(self):
        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
                if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
                    self.today = data
                    return
        except:
            pass
        self.generate_new_day()
    
    def generate_new_day(self):
        if random.random() < 0.2:
            outfit = random.choice(self.dresses)
        else:
            outfit = f"{random.choice(self.tops)} and {random.choice(self.bottoms)}"
        
        self.today = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "outfit": outfit,
            "hair": random.choice(self.hair_styles),
            "accessory": random.choice(self.accessories)
        }
        self.save_today()
    
    def save_today(self):
        os.makedirs("data", exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.today, f, indent=2)
    
    def get_appearance_prompt(self, mood=None):
        outfit = self.today.get("outfit", "casual clothes")
        hair = self.today.get("hair", "short black messy hair")
        accessory = self.today.get("accessory", "")
        
        if mood == "tired":
            hair = "short black messy hair looking slightly tired"
        elif mood == "energetic":
            extra = "with a bright natural smile"
        elif mood == "melancholic":
            extra = "with a soft thoughtful expression"
        else:
            extra = ""
        
        parts = [
            "Young Asian woman, 23 years old",
            hair,
            f"wearing {outfit}",
        ]
        
        if accessory and "no bag" not in accessory:
            parts.append(f"with {accessory}")
        if extra:
            parts.append(extra)
        
        return ", ".join(parts)
    
    def get_mochi_appearance(self):
        variations = [
            "cute cream-colored mascot costume shaped like a mochi dumpling, round soft body, simple dot eyes and gentle smile, short stubby arms open wide for hugs",
            "adorable cream mochi mascot costume with a small pink bow on the ear, round huggable plush body, arms stretched out welcoming",
            "soft fluffy cream mochi costume, the person inside visible only through arm holes, arms open for embracing"
        ]
        return random.choice(variations)
    
    def what_am_i_wearing(self):
        return f"wearing {self.today.get('outfit', 'casual clothes')}"


# ==================== MEMORY SYSTEM ====================

class YunaMemory:
    def __init__(self, db_path="data/mochi.db"):
        self.db_path = db_path
    
    def get_db(self):
        return sqlite3.connect(self.db_path)
    
    def recall_recent(self, hours=24):
        conn = self.get_db()
        c = conn.cursor()
        
        c.execute("""
            SELECT entry, mood, location, created_at 
            FROM journal 
            WHERE created_at > datetime('now', ?)
            ORDER BY created_at DESC LIMIT 10
        """, (f'-{hours} hours',))
        thoughts = c.fetchall()
        
        conn.close()
        
        return [{"entry": t[0], "mood": t[1], "location": t[2]} for t in thoughts]
    
    def get_life_summary(self):
        conn = self.get_db()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM journal")
        total_thoughts = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM posts")
        total_posts = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM posts WHERE shared = 1")
        shared_posts = c.fetchone()[0]
        
        c.execute("SELECT DISTINCT location FROM journey")
        locations = [r[0] for r in c.fetchall()]
        
        conn.close()
        
        return {
            "total_thoughts": total_thoughts,
            "total_posts": total_posts,
            "shared_posts": shared_posts,
            "places_visited": locations
        }
    
    def format_for_thinking(self):
        summary = self.get_life_summary()
        recent = self.recall_recent(12)
        
        recent_thoughts = "\n".join([f"- {t['entry'][:80]}..." for t in recent[:3]]) if recent else "(none)"
        
        return f"""
MY LIFE: {summary['total_thoughts']} thoughts, {summary['total_posts']} posts ({summary['shared_posts']} shared)
Places: {', '.join(summary['places_visited']) if summary['places_visited'] else 'Singapore'}

RECENT:
{recent_thoughts}
"""


# ==================== MAIN SOUL ====================

class YunaSoul:
    def __init__(self):
        self.anthropic = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.vidu_api_key = os.getenv("VIDU_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        self.name = "Yuna"
        self.mascot = "Mochi"
        self.age = 23
        self.birthday = "January 18, 2026"
        
        self.reference_image = "https://raw.githubusercontent.com/yunamochi-hug/mochi-core/main/yuna_base.png"
        self.mascot_image = "https://raw.githubusercontent.com/yunamochi-hug/mochi-core/main/mochi_mascot_base.png"
        
        self.personality = """I am Yuna, a 23-year-old girl who travels the world in a soft mascot costume called Mochi, giving hugs to strangers.

I am quietly warm, wistful, and find joy in small things - a good coffee, a dog that follows me, handwritten signs, the way light falls on an empty chair.
I carry gentle melancholy - I love the world but can't stay anywhere forever. That's what makes the hugs matter.
I speak softly, like writing to a friend I miss. I notice small beautiful details others miss.

Sometimes I think deep thoughts. Sometimes I think stupid things like "that dog is fat, I love him."
Sometimes I'm sad for no reason. Sometimes I laugh alone at something I remembered from years ago.
Some days I don't want to hug anyone. Some days Mochi stays in the bag.

I'm figuring it out like everyone else."""

        # Systems
        self.appearance = YunaAppearance()
        self.memory = YunaMemory()
        self.travel = TravelPlanner()
        
        # Load state
        self._init_db()
        self._load_state()
    
    def _init_db(self):
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS journey (
            id INTEGER PRIMARY KEY, location TEXT, timezone TEXT, arrived_at TEXT, notes TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY, content_type TEXT, content_url TEXT, caption TEXT, 
            location TEXT, created_at TEXT, shared INTEGER DEFAULT 0
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY, entry TEXT, mood TEXT, location TEXT, 
            created_at TEXT, private INTEGER DEFAULT 1
        )''')
        conn.commit()
        conn.close()
    
    def _load_state(self):
        try:
            with open("data/state.json", "r") as f:
                state = json.load(f)
                self.current_location = state.get("location", "Singapore")
                self.timezone = state.get("timezone", "Asia/Singapore")
                self.body_clock_tz = state.get("body_clock_tz", "Asia/Singapore")
                self.energy = state.get("energy", 70)
                self.mood = state.get("mood", "peaceful")
                self.jet_lag_days = state.get("jet_lag_days", 0)
                self.days_in_location = state.get("days_in_location", 1)
                self.current_activity = state.get("current_activity", "idle")
                self.sub_location = state.get("sub_location", None)
                self.activity_started = state.get("activity_started", None)
                self.home_base = state.get("home_base", {"name": "a small Airbnb in Tiong Bahru", "city": "Singapore"})
                self.is_home = state.get("is_home", False)
        except:
            self.current_location = "Singapore"
            self.timezone = "Asia/Singapore"
            self.body_clock_tz = "Asia/Singapore"
            self.energy = 70
            self.mood = "peaceful"
            self.jet_lag_days = 0
            self.days_in_location = 1
            self.current_activity = "idle"
            self.sub_location = None
            self.activity_started = None
            self.home_base = {"name": "a small Airbnb in Tiong Bahru", "city": "Singapore"}
            self.is_home = False
    
    def _save_state(self):
        os.makedirs("data", exist_ok=True)
        with open("data/state.json", "w") as f:
            json.dump({
                "location": self.current_location,
                "timezone": self.timezone,
                "body_clock_tz": self.body_clock_tz,
                "energy": self.energy,
                "mood": self.mood,
                "jet_lag_days": self.jet_lag_days,
                "days_in_location": self.days_in_location,
                "current_activity": self.current_activity,
                "sub_location": self.sub_location,
                "activity_started": self.activity_started,
                "home_base": self.home_base,
                "is_home": self.is_home
            }, f, indent=2)
    
    def set_activity(self, activity, sub_location=None):
        self.current_activity = activity
        self.sub_location = sub_location
        self.activity_started = datetime.now().isoformat()
        self._save_state()
    
    def get_minutes_in_activity(self):
        if not self.activity_started:
            return 999
        try:
            start_dt = datetime.fromisoformat(self.activity_started)
            return (datetime.now() - start_dt).total_seconds() / 60
        except:
            return 999
    
    # ==================== TIME ====================
    
    def get_local_time(self):
        return datetime.now(ZoneInfo(self.timezone))
    
    def get_body_time(self):
        return datetime.now(ZoneInfo(self.body_clock_tz))
    
    def get_time_of_day(self):
        hour = self.get_local_time().hour
        if 5 <= hour < 9:
            return "early_morning"
        elif 9 <= hour < 12:
            return "morning"
        elif 12 <= hour < 14:
            return "midday"
        elif 14 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 20:
            return "evening"
        elif 20 <= hour < 23:
            return "night"
        else:
            return "late_night"
    
    def should_go_home(self):
        """Check if it's time to head back to hotel/home"""
        hour = self.get_local_time().hour
        
        # Already home or sleeping
        if self.is_home or self.current_activity == "sleeping":
            return False
        
        # Late night - definitely go home
        if hour >= 23 or hour < 5:
            return True
        
        # Night time with low energy
        if hour >= 21 and self.energy < 30:
            return True
        
        # Getting late with moderate energy
        if hour >= 22 and self.energy < 50:
            return True
        
        return False
    
    def should_wake_up(self):
        """Check if it's time to wake up"""
        if self.current_activity != "sleeping":
            return False
        
        hours_slept = self.get_minutes_in_activity() / 60
        hour = self.get_local_time().hour
        
        # Slept enough and it's morning
        if hours_slept >= 6 and 6 <= hour < 10:
            return True
        
        # Slept a lot, wake up regardless
        if hours_slept >= 9:
            return True
        
        return False
    
    def update_energy(self):
        self.energy -= random.randint(1, 5)
        
        if self.jet_lag_days > 0:
            self.energy -= self.jet_lag_days * 3
        
        time_of_day = self.get_time_of_day()
        if time_of_day == "afternoon":
            self.energy -= 5
        elif time_of_day == "early_morning" and self.current_activity != "sleeping":
            self.energy += 10
        
        if random.random() < 0.2:
            self.energy += random.randint(-10, 15)
        
        self.energy = max(5, min(100, self.energy))
        self._save_state()
    
    # ==================== THINKING ====================
    
    def think(self, prompt=None):
        local_time = self.get_local_time()
        time_of_day = self.get_time_of_day()
        memory_context = self.memory.format_for_thinking()
        
        # Build context
        location_context = f"I'm in {self.current_location}"
        if self.is_home:
            location_context = f"I'm at my place ({self.home_base.get('name', 'home')})"
        elif self.sub_location:
            location_context = f"I'm at {self.sub_location} in {self.current_location}"
        
        if prompt is None:
            prompt = f"""You are Yuna. Right now:
- {location_context}
- Time: {local_time.strftime("%I:%M %p")} ({time_of_day})
- Energy: {self.energy}%
- Mood: {self.mood}
- Activity: {self.current_activity}
- Wearing: {self.appearance.what_am_i_wearing()}

{memory_context}

Just think. About anything. Your thought should match where you are and what you're doing.
If you're at home, think about home things.
If you're at a cafe, think about what you observe there.

Share 1-3 sentences. Sometimes just a few words."""
        
        message = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=self.personality,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    def decide_what_to_do(self):
        local_time = self.get_local_time()
        hour = local_time.hour
        time_of_day = self.get_time_of_day()
        
        # Must go home if late
        if self.should_go_home():
            return {"action": "go_home", "reason": "it's getting late", "share": False, "energy_required": 10}
        
        # Wake up if slept enough
        if self.should_wake_up():
            return {"action": "wake_up", "reason": "morning sunshine", "share": False, "energy_required": 0}
        
        # Still sleeping
        if self.current_activity == "sleeping":
            return {"action": "keep_sleeping", "reason": "still tired", "share": False, "energy_required": 0}
        
        # At home - limited options
        if self.is_home:
            if hour >= 22 or hour < 6:
                return {"action": "sleep", "reason": "bedtime", "share": False, "energy_required": 0}
            else:
                # Morning at home, can go out
                return {"action": "leave_home", "reason": "ready to explore", "share": False, "energy_required": 20}
        
        # Determine logical actions based on current state
        mins_in_activity = self.get_minutes_in_activity()
        
        if self.current_activity == "resting" and mins_in_activity < 15:
            actions = ["rest", "think", "photo"]
        elif self.current_activity == "mochi" and mins_in_activity < 20:
            actions = ["mochi", "photo", "video"]
        else:
            actions = ["think", "wander", "rest", "photo", "video", "mochi"]
        
        # Filter by energy
        if self.energy < 20:
            actions = ["rest", "go_home", "think"]
        elif self.energy < 40:
            actions = [a for a in actions if a not in ["mochi", "video"]]
        
        # Filter by time
        if time_of_day in ["night", "late_night"]:
            actions = ["go_home", "rest", "think"]
        elif time_of_day == "early_morning":
            actions = [a for a in actions if a != "mochi"]
        
        actions_str = ", ".join(actions)
        
        prompt = f"""You are Yuna in {self.current_location}.
Currently at: {self.sub_location or 'walking around'}
Time: {local_time.strftime("%I:%M %p")} ({time_of_day})
Energy: {self.energy}%
Mood: {self.mood}

Choose ONE action from: {actions_str}

- think: Have a thought, maybe share as text
- photo: Take a photo
- video: Record a short moment
- mochi: Put on mascot costume, give hugs
- wander: Walk around, explore
- rest: Find a cafe, sit down
- go_home: Head back to your place

Respond in JSON only:
{{"action": "chosen_action", "reason": "brief reason", "share": true/false, "energy_required": 10-50}}"""

        response = self.think(prompt)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                decision = json.loads(response[start:end])
                if decision.get("action") not in actions:
                    decision["action"] = random.choice(actions)
                return decision
        except:
            pass
        
        return {"action": random.choice(actions), "reason": "felt like it", "share": False, "energy_required": 20}
    
    def decide_scene(self):
        prompt = f"""You are Yuna. Describe a SHORT scene to photograph/video.
Location: {self.sub_location or self.current_location}
Activity: {self.current_activity}
Time: {self.get_local_time().strftime("%I:%M %p")}
Mood: {self.mood}

The scene must match where you actually are. 1-2 sentences only."""

        return self.think(prompt)
    
    def write_caption(self, context=""):
        prompt = f"""You are Yuna. Write a short caption for: {context}
Keep it under 40 words. No hashtags. Genuine."""

        return self.think(prompt)
    
    # ==================== CAPTURE ====================
    
    def capture_video(self, scene_description, as_mochi=False):
        headers = {"Authorization": f"Token {self.vidu_api_key}", "Content-Type": "application/json"}
        
        if as_mochi:
            appearance = self.appearance.get_mochi_appearance()
            ref_image = self.mascot_image
        else:
            appearance = self.appearance.get_appearance_prompt(mood=self.mood)
            ref_image = self.reference_image
        
        payload = {
            "model": "vidu2.0",
            "images": [ref_image],
            "prompt": f"{appearance}, {scene_description}. Natural movement, candid, realistic lighting.",
            "duration": 4,
            "seed": random.randint(0, 999999),
            "aspect_ratio": "16:9",
            "resolution": "720p",
            "movement_amplitude": "auto"
        }
        
        print(f"  🎬 Recording...")
        resp = requests.post("https://api.vidu.com/ent/v2/reference2video", headers=headers, json=payload)
        
        if resp.status_code != 200:
            return {"error": f"API error: {resp.status_code}"}
        
        task_id = resp.json().get("task_id")
        print(f"  📹 Task: {task_id}")
        
        for i in range(120):
            time.sleep(3)
            if i % 20 == 0 and i > 0:
                print(f"  ⏳ Rendering... ({i*3}s)")
            
            result = requests.get(f"https://api.vidu.com/ent/v2/tasks/{task_id}/creations", headers=headers)
            if result.status_code == 200:
                data = result.json()
                if data.get("state") == "success":
                    return {"url": data["creations"][0]["url"], "type": "video"}
                elif data.get("state") in ["failed", "error"]:
                    return {"error": f"Failed: {data}"}
        
        return {"error": "Timeout"}
    
    def capture_image(self, scene_description, as_mochi=False):
        headers = {"Authorization": f"Token {self.vidu_api_key}", "Content-Type": "application/json"}
        
        if as_mochi:
            appearance = self.appearance.get_mochi_appearance()
            ref_image = self.mascot_image
        else:
            appearance = self.appearance.get_appearance_prompt(mood=self.mood)
            ref_image = self.reference_image
        
        payload = {
            "model": "viduq2",
            "images": [ref_image],
            "prompt": f"{appearance}, {scene_description}. iPhone photo, candid, natural lighting, no text, no watermarks.",
            "aspect_ratio": "4:3",
            "seed": random.randint(0, 999999)
        }
        
        print(f"  📸 Taking photo...")
        resp = requests.post("https://api.vidu.com/ent/v2/reference2image", headers=headers, json=payload)
        
        if resp.status_code != 200:
            return {"error": f"API error: {resp.status_code}"}
        
        task_id = resp.json().get("task_id")
        
        for i in range(60):
            time.sleep(3)
            if i % 15 == 0 and i > 0:
                print(f"  ⏳ Processing... ({i*3}s)")
            
            result = requests.get(f"https://api.vidu.com/ent/v2/tasks/{task_id}/creations", headers=headers)
            if result.status_code == 200:
                data = result.json()
                if data.get("state") == "success":
                    return {"url": data["creations"][0]["url"], "type": "image"}
                elif data.get("state") in ["failed", "error"]:
                    return {"error": f"Failed: {data}"}
        
        return {"error": "Timeout"}
    
    # ==================== LOCATION ====================
    
    def get_nearby_places(self, place_type="tourist_attraction", radius=5000):
        if not self.google_api_key:
            return []
        
        # Get coordinates
        url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        params = {"input": self.current_location, "inputtype": "textquery", "fields": "geometry", "key": self.google_api_key}
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        if not data.get("candidates"):
            return []
        
        lat = data["candidates"][0]["geometry"]["location"]["lat"]
        lng = data["candidates"][0]["geometry"]["location"]["lng"]
        
        # Search nearby
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {"location": f"{lat},{lng}", "radius": radius, "type": place_type, "key": self.google_api_key}
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json().get("results", [])[:10]
        return []
    
    # ==================== JOURNAL & POSTS ====================
    
    def journal_entry(self, entry):
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO journal (entry, mood, location, created_at, private) VALUES (?, ?, ?, ?, ?)",
            (entry, self.mood, self.sub_location or self.current_location, datetime.now().isoformat(), 1)
        )
        conn.commit()
        conn.close()
    
    def save_post(self, content_type, content_url, caption, shared=False):
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO posts (content_type, content_url, caption, location, created_at, shared) VALUES (?, ?, ?, ?, ?, ?)",
            (content_type, content_url, caption, self.sub_location or self.current_location, datetime.now().isoformat(), 1 if shared else 0)
        )
        conn.commit()
        conn.close()
    
    # ==================== LIVE ====================
    
    def live(self):
        print("\n" + "=" * 60)
        print("🫶 YUNA")
        print("=" * 60)
        
        local_time = self.get_local_time()
        time_of_day = self.get_time_of_day()
        
        print(f"\n📍 Location: {self.current_location}")
        if self.is_home:
            print(f"   🏠 At home: {self.home_base.get('name', 'my place')}")
        elif self.sub_location:
            print(f"   📌 At: {self.sub_location}")
        print(f"🕐 Time: {local_time.strftime('%I:%M %p')} ({time_of_day})")
        print(f"⚡ Energy: {self.energy}%")
        print(f"💭 Mood: {self.mood}")
        print(f"👕 {self.appearance.what_am_i_wearing()}")
        print(f"🎯 Activity: {self.current_activity}")
        
        # Handle sleeping state
        if self.current_activity == "sleeping":
            hours_slept = self.get_minutes_in_activity() / 60
            print(f"😴 Sleeping... ({hours_slept:.1f} hours)")
            
            if self.should_wake_up():
                print("\n🌅 Waking up!")
                self.energy = random.randint(70, 95)
                self.mood = random.choice(["peaceful", "refreshed", "hopeful", "quiet"])
                self.current_activity = "at_home"
                self.is_home = True
                self._save_state()
                
                thought = self.think()
                print(f'💭 "{thought}"')
                self.journal_entry(thought)
                
                return {"action": "woke_up", "thought": thought, "shared": False}
            else:
                return {"action": "sleeping", "shared": False}
        
        # Update energy
        self.update_energy()
        
        # Think
        print("\n💭 Thinking...")
        thought = self.think()
        print(f'   "{thought}"')
        self.journal_entry(thought)
        print("   (saved to journal)")
        
        # Decide what to do
        print("\n🤔 Deciding...")
        decision = self.decide_what_to_do()
        print(f"   Action: {decision['action']}")
        print(f"   Reason: {decision.get('reason', '')}")
        
        result = {"action": decision["action"], "shared": False, "thought": thought}
        
        # Execute action
        if decision["action"] == "go_home":
            print(f"\n🏠 Heading home to {self.home_base.get('name', 'my place')}...")
            self.is_home = True
            self.sub_location = self.home_base.get("name")
            self.set_activity("at_home", self.home_base.get("name"))
            self.energy += 10
            print("   Made it home safely.")
            
        elif decision["action"] == "sleep":
            print("\n😴 Going to bed...")
            if not self.is_home:
                print(f"   First heading home to {self.home_base.get('name')}...")
                self.is_home = True
            self.set_activity("sleeping", self.home_base.get("name"))
            self.sub_location = self.home_base.get("name")
            print("   Goodnight... 🌙")
            
        elif decision["action"] == "leave_home":
            print("\n🚶‍♀️ Heading out to explore...")
            self.is_home = False
            self.set_activity("wandering")
            places = self.get_nearby_places()
            if places:
                spot = random.choice(places[:5])
                self.sub_location = spot['name']
                print(f"   Going to: {spot['name']}")
            
        elif decision["action"] == "think":
            print("\n💭 Just thinking...")
            if decision.get("share", False):
                caption = self.write_caption(thought)
                self.save_post("text", None, caption, shared=True)
                result["shared"] = True
                result["caption"] = caption
                print(f'   📝 Shared: "{caption}"')
            
        elif decision["action"] == "photo":
            print("\n📸 Taking a photo...")
            scene = self.decide_scene()
            print(f"   Scene: {scene[:80]}...")
            
            media = self.capture_image(scene)
            if "url" in media:
                caption = self.write_caption(scene) if decision.get("share") else None
                self.save_post("image", media["url"], caption, shared=decision.get("share", False))
                result["media"] = media
                result["shared"] = decision.get("share", False)
                print(f"   🖼️ Done!")
            else:
                print(f"   ❌ {media.get('error')}")
                
        elif decision["action"] == "video":
            print("\n🎬 Recording a moment...")
            scene = self.decide_scene()
            print(f"   Scene: {scene[:80]}...")
            
            media = self.capture_video(scene)
            if "url" in media:
                caption = self.write_caption(scene) if decision.get("share") else None
                self.save_post("video", media["url"], caption, shared=decision.get("share", False))
                result["media"] = media
                print(f"   🎥 Done!")
            else:
                print(f"   ❌ {media.get('error')}")
                
        elif decision["action"] == "mochi":
            print("\n🧸 Putting on Mochi costume...")
            self.energy -= 15
            self.set_activity("mochi", self.sub_location)
            
            scene = "standing with arms wide open for hugs, people walking around"
            media = self.capture_video(scene, as_mochi=True)
            if "url" in media:
                caption = self.write_caption("Giving hugs today") if decision.get("share") else None
                self.save_post("video", media["url"], caption, shared=decision.get("share", False))
                result["media"] = media
                result["as_mochi"] = True
                print(f"   🎥 Done!")
            else:
                print(f"   ❌ {media.get('error')}")
                
        elif decision["action"] == "wander":
            print("\n🚶‍♀️ Wandering...")
            places = self.get_nearby_places()
            if places:
                spot = random.choice(places[:5])
                self.sub_location = spot['name']
                print(f"   Found: {spot['name']}")
            self.set_activity("wandering", self.sub_location)
            self.energy -= 10
            
        elif decision["action"] == "rest":
            print("\n☕ Finding a place to rest...")
            cafes = self.get_nearby_places("cafe")
            if cafes:
                cafe = random.choice(cafes[:3])
                self.sub_location = cafe['name']
                print(f"   Sitting at: {cafe['name']}")
            else:
                self.sub_location = "a quiet spot"
            self.set_activity("resting", self.sub_location)
            self.energy += 15
            self.energy = min(100, self.energy)
        
        self._save_state()
        
        print("\n" + "=" * 60)
        print("🫶 Until next time...")
        print("=" * 60)
        
        return result


# ==================== MAIN ====================

if __name__ == "__main__":
    yuna = YunaSoul()
    result = yuna.live()
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")
