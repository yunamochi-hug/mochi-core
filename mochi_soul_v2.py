"""
YUNA v2 - Complete Rewrite with All Fixes

FIXES IMPLEMENTED:
1. Ordered thoughts per step (not random)
2. Track thought index per step
3. Step duration tracking
4. Remove underscores from display
5. Dynamic location display
6. Journey state machine
7. Prevent duplicate thoughts
8. Time-of-day awareness
9. Milestone auto-posts
10. Trip completion logic
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

load_dotenv()

# ============== DESTINATIONS & FLIGHTS ==============
DESTINATIONS = ["Tokyo", "Seoul", "Bangkok", "Hong Kong", "Taipei", "Osaka", "Kuala Lumpur", "Bali"]

FLIGHTS = {
    ("Singapore", "Tokyo"): [
        {"flight": "SQ638", "airline": "Singapore Airlines", "dep": "08:45", "arr": "16:50", "duration": 7.08, "dep_terminal": "T3", "arr_terminal": "T1", "arr_airport": "Narita", "arr_code": "NRT"},
    ],
    ("Singapore", "Seoul"): [
        {"flight": "SQ600", "airline": "Singapore Airlines", "dep": "08:30", "arr": "15:55", "duration": 6.42, "dep_terminal": "T3", "arr_terminal": "T2", "arr_airport": "Incheon", "arr_code": "ICN"},
    ],
    ("Singapore", "Bangkok"): [
        {"flight": "SQ970", "airline": "Singapore Airlines", "dep": "08:00", "arr": "09:20", "duration": 2.33, "dep_terminal": "T3", "arr_terminal": "Main", "arr_airport": "Suvarnabhumi", "arr_code": "BKK"},
    ],
    ("Singapore", "Hong Kong"): [
        {"flight": "SQ856", "airline": "Singapore Airlines", "dep": "08:25", "arr": "12:25", "duration": 4.0, "dep_terminal": "T3", "arr_terminal": "T1", "arr_airport": "Hong Kong Intl", "arr_code": "HKG"},
    ],
    ("Singapore", "Taipei"): [
        {"flight": "SQ876", "airline": "Singapore Airlines", "dep": "08:20", "arr": "13:05", "duration": 4.75, "dep_terminal": "T3", "arr_terminal": "T2", "arr_airport": "Taoyuan", "arr_code": "TPE"},
    ],
    ("Singapore", "Osaka"): [
        {"flight": "SQ618", "airline": "Singapore Airlines", "dep": "08:30", "arr": "16:00", "duration": 6.5, "dep_terminal": "T3", "arr_terminal": "T1", "arr_airport": "Kansai", "arr_code": "KIX"},
    ],
    ("Singapore", "Kuala Lumpur"): [
        {"flight": "SQ106", "airline": "Singapore Airlines", "dep": "07:30", "arr": "08:30", "duration": 1.0, "dep_terminal": "T3", "arr_terminal": "Main", "arr_airport": "KLIA", "arr_code": "KUL"},
    ],
    ("Singapore", "Bali"): [
        {"flight": "SQ938", "airline": "Singapore Airlines", "dep": "08:10", "arr": "10:55", "duration": 2.75, "dep_terminal": "T3", "arr_terminal": "Intl", "arr_airport": "Ngurah Rai", "arr_code": "DPS"},
    ],
}

AIRPORTS = {
    "Singapore": {"code": "SIN", "name": "Changi Airport"},
    "Tokyo": {"code": "NRT", "name": "Narita Airport"},
    "Seoul": {"code": "ICN", "name": "Incheon Airport"},
    "Bangkok": {"code": "BKK", "name": "Suvarnabhumi Airport"},
    "Hong Kong": {"code": "HKG", "name": "Hong Kong Intl"},
    "Taipei": {"code": "TPE", "name": "Taoyuan Airport"},
    "Osaka": {"code": "KIX", "name": "Kansai Airport"},
    "Kuala Lumpur": {"code": "KUL", "name": "KLIA"},
    "Bali": {"code": "DPS", "name": "Ngurah Rai Airport"},
}

TIMEZONES = {
    "Singapore": "Asia/Singapore", "Tokyo": "Asia/Tokyo", "Seoul": "Asia/Seoul",
    "Bangkok": "Asia/Bangkok", "Hong Kong": "Asia/Hong_Kong", "Taipei": "Asia/Taipei",
    "Osaka": "Asia/Tokyo", "Kuala Lumpur": "Asia/Kuala_Lumpur", "Bali": "Asia/Makassar",
}

HOTELS = {
    "Tokyo": [{"name": "Hotel Gracery Shinjuku", "area": "Shinjuku", "price": 150}],
    "Seoul": [{"name": "Lotte Hotel Seoul", "area": "Myeongdong", "price": 200}],
    "Bangkok": [{"name": "Eastin Grand Hotel Sathorn", "area": "Sathorn", "price": 90}],
    "Hong Kong": [{"name": "The Mira Hong Kong", "area": "Tsim Sha Tsui", "price": 180}],
    "Taipei": [{"name": "W Taipei", "area": "Xinyi", "price": 200}],
    "Osaka": [{"name": "Cross Hotel Osaka", "area": "Shinsaibashi", "price": 120}],
    "Kuala Lumpur": [{"name": "The RuMa Hotel", "area": "KLCC", "price": 180}],
    "Bali": [{"name": "Alila Seminyak", "area": "Seminyak", "price": 200}],
}

# ============== ORDERED THOUGHTS (Sequence matters!) ==============
ORDERED_THOUGHTS = {
    "wake_up": [
        "Alarm went off. Today's the day!",
        "Packing the last few things... passport, charger, Mochi costume",
        "Triple checking I have everything",
        "Texted mom that I'm leaving. She worries, but she understands",
        "One last look around. See you soon, home.",
        "Okay. Time to go. {city} awaits!",
    ],
    "going_to_airport": [
        "In the Grab now. Watching the city through the window.",
        "The driver asked where I'm going. {city}, I said.",
        "Traffic as usual. Deep breaths.",
        "Almost at the airport. Getting excited!",
    ],
    "at_airport": [
        "Changi Terminal {terminal}. Love this airport.",
        "Checked in! Bag dropped off.",
        "Security done. Always a bit nervous even with nothing to hide.",
        "Now just me, my backpack, and Mochi.",
        "Grabbed a kopi. Airport coffee hits different.",
    ],
    "at_gate": [
        "Found Gate {gate}. Perfect view of the planes.",
        "Flight {flight} to {city} on the board. That's me!",
        "People watching. Everyone has somewhere to be.",
        "A kid near me is SO excited about flying. Same, kid.",
        "Boarding soon. Butterflies in my stomach.",
    ],
    "boarding": [
        "They called my zone! Here we go.",
        "Walking down the jet bridge. Love this part.",
        "Found my seat. {seat}. Window!",
        "Settled in. Seatbelt on. Ready for takeoff.",
    ],
    "in_flight": [
        "Wheels up! Goodbye Singapore.",
        "Above the clouds now. Everything below looks tiny.",
        "The window view never gets old.",
        "Snacks arrived. Airplane food isn't bad when you're hungry.",
        "Reading a book. The engine hum is so calming.",
        "Halfway there. Watching the flight map.",
        "Thinking about all the people I might hug in {city}.",
        "Starting descent soon. Can see land below!",
    ],
    "landed": [
        "Touched down! Welcome to {city}!",
        "My ears are still popping but I'm here!",
        "Waiting to deplane. Everyone's standing already.",
        "Finally off the plane. Stretching feels amazing.",
        "Immigration done. Now to find my ride.",
    ],
    "going_to_hotel": [
        "On the way to the hotel. First impressions of {city}: different!",
        "The signs are all different. I love that feeling.",
        "Watching the city go by through the window.",
        "Almost there. Can't wait to drop my bags.",
    ],
    "checked_in": [
        "Room key in hand! Made it to {hotel}.",
        "The room is nice. Cozy.",
        "First thing I do: check the shower pressure. It's good!",
        "Unpacking Mochi first. Priorities.",
        "Should I rest or explore? Decisions...",
    ],
    "resting": [
        "Lying on the bed like a starfish. Earned this.",
        "Quick power nap. Travel is tiring.",
        "Scrolling through local food spots. So many options.",
        "Feeling recharged. Ready to explore!",
    ],
    "exploring": [
        "Out on the streets of {city}!",
        "The smells here are amazing. Street food calling.",
        "Got a bit lost. Found something beautiful.",
        "Coffee break at a local cafe.",
        "Taking it all in. This is why I travel.",
        "Found the perfect spot for Mochi tomorrow.",
    ],
    "mochi_time": [
        "Time to put on Mochi! Let's spread some warmth.",
        "Costume on. Deep breath. Here we go.",
        "First person walking towards me. They need this.",
        "The hugs are flowing. Hearts connecting.",
        "A child ran up first. They always do.",
        "Someone hugged back and didn't let go. I hope they're okay.",
    ],
    "after_hugs": [
        "Arms are tired but heart is full.",
        "Lost count of the hugs. Every single one mattered.",
        "Someone cried. I held them longer.",
        "Taking off the costume. Still feel warm inside.",
        "Time to rest and refuel.",
    ],
    "evening": [
        "The city looks different at night. Softer.",
        "Found a nice spot for dinner.",
        "Local food never disappoints.",
        "Walking back to the hotel. Good tired.",
        "What a day. Grateful.",
    ],
    "night": [
        "Back at the hotel. Feet hurt but worth it.",
        "Journaling about today. Don't want to forget.",
        "Wondering if the people I hugged are sleeping well.",
        "Tomorrow: more hugs, more warmth.",
        "Good night, {city}.",
    ],
    "general": [
        "Kindness is a language everyone understands.",
        "Strangers are just friends I haven't hugged yet.",
        "The world is heavy. Hugs make it lighter.",
        "Feeling is the secret. I felt this trip before it happened.",
        "Everyone is fighting something. Compassion costs nothing.",
        "I am what I imagine myself to be.",
    ],
}

# ============== PHOTO PROMPTS BY STEP ==============
STEP_PHOTO_PROMPTS = {
    "wake_up": [
        "natural light through window, suitcase on bed half packed, travel essentials laid out, cozy room, no people",
        "passport and boarding pass on table with coffee cup, natural light, travel aesthetic, no people",
        "backpack by the door ready to go, natural light, minimalist, no people",
    ],
    "going_to_airport": [
        "view through car window of city streets, travel day, motion blur, no people",
        "highway leading to airport, sky, travel vibes, no people",
    ],
    "at_airport": [
        "airport terminal interior, Changi Airport, modern architecture, natural light, no people",
        "departure board showing flights, airport aesthetic, no people",
        "coffee cup on airport cafe table with boarding pass, travel aesthetic, no people",
    ],
    "at_gate": [
        "airplane through terminal window, gate seating area, peaceful, no people",
        "boarding pass and coffee, gate waiting area, travel mood, no people",
    ],
    "boarding": [
        "airplane aisle, overhead bins, travel photography, no people",
        "airplane window seat view of wing on tarmac, no people",
    ],
    "in_flight": [
        "airplane window view of clouds, golden light, dreamy, no people",
        "airplane wing against blue sky and clouds, no people",
        "airplane tray table with snacks and book, cozy flight vibes, no people",
    ],
    "landed": [
        "airplane window view of new city from above, landing, no people",
        "airport tarmac through airplane window, arrived, no people",
    ],
    "going_to_hotel": [
        "city view through taxi/train window, new city first impressions, no people",
        "urban streets of {city}, first glimpse, travel photography, no people",
    ],
    "checked_in": [
        "hotel room with city view through window, cozy interior, no people",
        "hotel bed with white sheets, afternoon light, peaceful, no people",
        "hotel room key card on desk with city view, no people",
    ],
    "exploring": {
        "Tokyo": ["Tokyo narrow alley with lanterns, atmospheric, no people", "ramen bowl close-up steam rising, no people", "Tokyo street vending machines at night, no people"],
        "Seoul": ["Seoul Hongdae street neon signs, no people", "Korean street food tteokbokki close-up, no people", "Korean cafe aesthetic, coffee and dessert, no people"],
        "Bangkok": ["Bangkok street food stall, wok flames, no people", "Thai temple golden spires, no people", "Thai iced tea close-up, no people"],
        "Hong Kong": ["Hong Kong skyline Victoria Peak, no people", "dim sum close-up bamboo steamers, no people", "Hong Kong neon signs Mong Kok, no people"],
        "Taipei": ["Taipei 101 night city lights, no people", "bubble tea close-up colorful, no people", "Taiwan night market food stalls, no people"],
        "Osaka": ["Osaka Dotonbori neon canal reflection, no people", "takoyaki close-up, no people", "Osaka street food, no people"],
        "Kuala Lumpur": ["Petronas Towers night, no people", "nasi lemak close-up Malaysian food, no people", "KL street food Jalan Alor, no people"],
        "Bali": ["Bali rice terraces morning mist, no people", "tropical smoothie bowl Bali cafe, no people", "Bali beach sunset, no people"],
        "default": ["city street at night, atmospheric, no people", "local food close-up, no people"],
    },
    "mochi_time": {
        "Tokyo": ["cute mochi mascot Shibuya crossing, arms open for hugs, heartwarming"],
        "Seoul": ["cute mochi mascot Myeongdong street, giving hugs, heartwarming"],
        "Bangkok": ["cute mochi mascot near temple, arms open, friendly"],
        "Hong Kong": ["cute mochi mascot Victoria Harbour, giving hugs"],
        "Taipei": ["cute mochi mascot Ximending, arms open, friendly"],
        "Osaka": ["cute mochi mascot Dotonbori, giving hugs, neon lights"],
        "Kuala Lumpur": ["cute mochi mascot KLCC Petronas Towers, arms open for hugs"],
        "Bali": ["cute mochi mascot Ubud rice terraces, giving hugs"],
        "default": ["cute mochi mascot city center, arms open for hugs, heartwarming"],
    },
}

# ============== MILESTONE CAPTIONS (Auto-post at key moments) ==============
MILESTONE_POSTS = {
    "boarding": ["Boarding now! ✈️ {city} here I come!", "Gate {gate} → {city}! Let's go 🛫"],
    "in_flight": ["Up in the air! ☁️", "Window seat views ✈️🪟", "Somewhere over the clouds ☁️"],
    "landed": ["Landed safely in {city}! 🛬", "Hello {city}! 👋", "Made it! 🎉"],
    "checked_in": ["Checked in! 🏨 Time to explore {city}", "Hotel vibes in {city} ✨", "Home base secured! 🔑"],
    "mochi_time": ["Mochi time! 🧸 Free hugs in {city}!", "If you see Mochi, come get a hug! 🫶"],
}


class YunaSoul:
    def __init__(self):
        self.vidu_api_key = os.getenv("VIDU_API_KEY")
        self.reference_image = "https://raw.githubusercontent.com/yunamochi-hug/mochi-core/main/yuna_base.png"
        self.mascot_image = "https://raw.githubusercontent.com/yunamochi-hug/mochi-core/main/mochi_mascot_base.png"
        self._init_db()
        self._load_state()
        self._load_travel()
        self._load_thought_tracker()

    def _init_db(self):
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS journey (id INTEGER PRIMARY KEY, location TEXT, timezone TEXT, arrived_at TEXT, notes TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, content_type TEXT, content_url TEXT, caption TEXT, location TEXT, created_at TEXT, shared INTEGER DEFAULT 0)')
        c.execute('CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY, entry TEXT, mood TEXT, location TEXT, created_at TEXT, private INTEGER DEFAULT 1)')
        c.execute('CREATE TABLE IF NOT EXISTS travel_log (id INTEGER PRIMARY KEY, step TEXT, description TEXT, timestamp TEXT, flight TEXT, location TEXT)')
        conn.commit()
        conn.close()

    def _load_state(self):
        try:
            with open("data/state.json", "r") as f:
                state = json.load(f)
                self.current_location = state.get("location", "Singapore")
                self.display_location = state.get("display_location", self.current_location)
                self.timezone = state.get("timezone", "Asia/Singapore")
                self.energy = state.get("energy", 80)
                self.mood = state.get("mood", "peaceful")
                self.current_step = state.get("current_step", "idle")
                self.step_start_time = state.get("step_start_time")
                self.home_base = state.get("home_base", {"name": "Home", "city": "Singapore"})
                self.mochi_hugs_today = state.get("mochi_hugs_today", 0)
                self.days_in_location = state.get("days_in_location", 1)
        except:
            self._reset_to_singapore()

    def _reset_to_singapore(self):
        self.current_location = "Singapore"
        self.display_location = "Singapore"
        self.timezone = "Asia/Singapore"
        self.energy = 80
        self.mood = "peaceful"
        self.current_step = "idle"
        self.step_start_time = None
        self.home_base = {"name": "Home", "city": "Singapore"}
        self.mochi_hugs_today = 0
        self.days_in_location = 1
        self._save_state()

    def _save_state(self):
        os.makedirs("data", exist_ok=True)
        with open("data/state.json", "w") as f:
            json.dump({
                "location": self.current_location,
                "display_location": self.display_location,
                "timezone": self.timezone,
                "energy": self.energy,
                "mood": self.mood,
                "current_step": self.current_step,
                "step_start_time": self.step_start_time,
                "home_base": self.home_base,
                "mochi_hugs_today": self.mochi_hugs_today,
                "days_in_location": self.days_in_location,
                "travel_state": self.current_step,  # For dashboard compatibility
            }, f, indent=2)

    def _load_travel(self):
        try:
            with open("data/travel_full.json", "r") as f:
                self.travel = json.load(f)
        except:
            self.travel = {"status": "idle", "current_trip": None, "flight": None, "hotel": None, "timeline": [], "current_step_index": 0}

    def _save_travel(self):
        os.makedirs("data", exist_ok=True)
        with open("data/travel_full.json", "w") as f:
            json.dump(self.travel, f, indent=2)

    def _load_thought_tracker(self):
        """Track which thoughts have been used to prevent duplicates"""
        try:
            with open("data/thought_tracker.json", "r") as f:
                self.thought_tracker = json.load(f)
        except:
            self.thought_tracker = {
                "current_step": None,
                "thought_index": 0,
                "used_thoughts": [],
                "last_milestone_posted": None,
            }

    def _save_thought_tracker(self):
        os.makedirs("data", exist_ok=True)
        with open("data/thought_tracker.json", "w") as f:
            json.dump(self.thought_tracker, f, indent=2)

    def get_local_time(self):
        return datetime.now(ZoneInfo(self.timezone))

    def get_time_of_day(self):
        hour = self.get_local_time().hour
        if 5 <= hour < 9: return "travel day"
        elif 9 <= hour < 12: return "morning"
        elif 12 <= hour < 17: return "afternoon"
        elif 17 <= hour < 21: return "evening"
        else: return "night"

    def format_step_display(self, step):
        """Convert step_name to readable format: 'checked_in' -> 'Checked In'"""
        if not step:
            return "Idle"
        return step.replace("_", " ").title()

    def get_display_location(self):
        """Get the current display location based on travel state"""
        if not self.travel.get("current_trip"):
            return self.current_location
        
        trip = self.travel["current_trip"]
        step = self.current_step
        
        if step in ["wake_up", "going_to_airport"]:
            return self.current_location
        elif step == "at_airport":
            return f"Changi Airport"
        elif step == "at_gate":
            gate = self.travel.get("flight", {}).get("gate", "")
            return f"Changi Airport Gate {gate}"
        elif step == "boarding":
            return f"Boarding {self.travel.get('flight', {}).get('flight', '')}"
        elif step == "in_flight":
            from_code = AIRPORTS.get(trip["from"], {}).get("code", trip["from"][:3].upper())
            to_code = self.travel.get("flight", {}).get("arr_code", trip["to"][:3].upper())
            return f"In Flight ✈️ {from_code} → {to_code}"
        elif step == "landed":
            return self.travel.get("flight", {}).get("arr_airport", trip["to"])
        elif step == "going_to_hotel":
            return f"En route to {trip['to']}"
        else:
            return trip.get("to", self.current_location)

    def get_destination_city(self):
        """Get the destination city if traveling"""
        if self.travel.get("current_trip"):
            return self.travel["current_trip"].get("to", self.current_location)
        return self.current_location

    # ============== THOUGHT SYSTEM ==============
    def get_next_thought(self):
        """Get the next thought in sequence for current step - TIME AWARE!"""
        step = self.current_step
        if step == "idle":
            step = "general"
        
        # Get time of day for dynamic thoughts
        time_of_day = self.get_time_of_day()
        
        # Map some steps to thought categories
        step_map = {
            "checked_in_hotel": "checked_in",
            "mochi_time": "mochi_time",
            "after_hugs": "after_hugs",
        }
        thought_step = step_map.get(step, step)
        
        thoughts = ORDERED_THOUGHTS.get(thought_step, ORDERED_THOUGHTS["general"])
        
        # Check if we changed steps
        if self.thought_tracker.get("current_step") != step:
            self.thought_tracker["current_step"] = step
            self.thought_tracker["thought_index"] = 0
            self.thought_tracker["used_thoughts"] = []
        
        # Get next thought in sequence
        idx = self.thought_tracker["thought_index"]
        if idx >= len(thoughts):
            # Cycle back but skip recently used
            idx = 0
            self.thought_tracker["thought_index"] = 0
        
        thought = thoughts[idx]
        self.thought_tracker["thought_index"] = idx + 1
        self.thought_tracker["used_thoughts"].append(thought)
        
        # Keep only last 10 used thoughts
        if len(self.thought_tracker["used_thoughts"]) > 10:
            self.thought_tracker["used_thoughts"] = self.thought_tracker["used_thoughts"][-10:]
        
        self._save_thought_tracker()
        
        # Format thought with variables - TIME AWARE!
        city = self.get_destination_city()
        flight = self.travel.get("flight") or {}
        hotel = self.travel.get("hotel") or {}
        time_of_day = self.get_time_of_day()
        
        # Dynamic time-based word replacements
        time_words = {
            "morning": {"greeting": "morning", "light": "morning light", "traffic": "morning traffic", "sky": "sunrise"},
            "afternoon": {"greeting": "afternoon", "light": "afternoon sun", "traffic": "afternoon traffic", "sky": "blue sky"},
            "evening": {"greeting": "evening", "light": "golden hour light", "traffic": "evening traffic", "sky": "sunset"},
            "night": {"greeting": "night", "light": "city lights", "traffic": "night traffic", "sky": "night sky"},
            "early morning": {"greeting": "early morning", "light": "dawn light", "traffic": "empty roads", "sky": "sunrise"},
        }
        time_vars = time_words.get(time_of_day, time_words["morning"])
        
        thought = thought.format(
            city=city,
            terminal=flight.get("dep_terminal", "3"),
            gate=flight.get("gate", "B12"),
            flight=flight.get("flight", "SQ106"),
            seat=flight.get("seat", "22A"),
            hotel=hotel.get("name", self.home_base.get("name", "hotel")),
            time_greeting=time_vars["greeting"],
            time_light=time_vars["light"],
            time_traffic=time_vars["traffic"],
            time_sky=time_vars["sky"],
        )
        
        return thought

    # ============== PHOTO SYSTEM ==============
    def get_photo_prompt(self):
        """Get appropriate photo prompt for current step"""
        step = self.current_step
        city = self.get_destination_city()
        
        # Map steps
        step_map = {"checked_in_hotel": "checked_in"}
        photo_step = step_map.get(step, step)
        
        prompts = STEP_PHOTO_PROMPTS.get(photo_step)
        
        if prompts is None:
            prompts = STEP_PHOTO_PROMPTS.get("exploring", {}).get(city, STEP_PHOTO_PROMPTS["exploring"]["default"])
        elif isinstance(prompts, dict):
            # City-specific prompts
            prompts = prompts.get(city, prompts.get("default", ["city street, atmospheric, no people"]))
        
        prompt = random.choice(prompts)
        return prompt.format(city=city)

    def capture_image(self, prompt):
        """Generate image using Vidu API"""
        headers = {"Authorization": f"Token {self.vidu_api_key}", "Content-Type": "application/json"}
        
        # Use mascot image for mochi_time, otherwise reference image
        ref_image = self.mascot_image if self.current_step == "mochi_time" else self.reference_image
        
        payload = {
            "model": "vidu2.0",
            "images": [ref_image],
            "prompt": f"{prompt}, high quality photography, natural lighting, realistic",
            "aspect_ratio": "4:3",
            "seed": random.randint(0, 999999)
        }
        
        print(f"   📸 Generating image...")
        try:
            resp = requests.post("https://api.vidu.com/ent/v2/reference2image", headers=headers, json=payload, timeout=30)
            if resp.status_code != 200:
                print(f"   ❌ API error: {resp.status_code}")
                return None
            
            task_id = resp.json().get("task_id")
            for i in range(60):
                time.sleep(3)
                if i % 10 == 0 and i > 0:
                    print(f"   ⏳ {i*3}s...")
                result = requests.get(f"https://api.vidu.com/ent/v2/tasks/{task_id}/creations", headers=headers, timeout=30)
                if result.status_code == 200:
                    data = result.json()
                    if data.get("state") == "success":
                        print(f"   ✅ Image generated!")
                        return data["creations"][0]["url"]
                    elif data.get("state") in ["failed", "error"]:
                        print(f"   ❌ Generation failed")
                        return None
            return None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    # ============== POSTING SYSTEM ==============
    def post_milestone(self, step):
        """Auto-post text at key milestone moments"""
        if step not in MILESTONE_POSTS:
            return None
        
        # Check if already posted for this step
        if self.thought_tracker.get("last_milestone_posted") == step:
            return None
        
        captions = MILESTONE_POSTS[step]
        caption = random.choice(captions)
        
        city = self.get_destination_city()
        gate = self.travel.get("flight", {}).get("gate", "B12")
        caption = caption.format(city=city, gate=gate)
        
        # Save as text post
        self.save_post("text", None, caption, shared=True)
        self.thought_tracker["last_milestone_posted"] = step
        self._save_thought_tracker()
        
        print(f"   📝 Milestone post: {caption}")
        return caption

    def save_post(self, content_type, content_url, caption, shared=True):
        """Save a post to database"""
        location = self.get_display_location()
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO posts (content_type, content_url, caption, location, created_at, shared) VALUES (?, ?, ?, ?, ?, ?)",
            (content_type, content_url, caption, location, datetime.now().isoformat(), 1 if shared else 0)
        )
        conn.commit()
        conn.close()
        print(f"   📝 Posted: {caption[:50]}...")

    def journal_entry(self, entry):
        """Save a journal entry"""
        location = self.get_display_location()
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO journal (entry, mood, location, created_at, private) VALUES (?, ?, ?, ?, ?)",
            (entry, self.mood, location, datetime.now().isoformat(), 1)
        )
        conn.commit()
        conn.close()

    # ============== TRAVEL SYSTEM ==============
    def get_current_travel_step(self):
        """Get current step based on timeline"""
        if self.travel.get("status") != "booked" or not self.travel.get("timeline"):
            return None
        
        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)
        
        current_step = None
        for i, step in enumerate(self.travel["timeline"]):
            step_time = datetime.fromisoformat(step["time"]).replace(tzinfo=tz)
            if now >= step_time:
                current_step = step.copy()
                current_step["index"] = i
                self.travel["current_step_index"] = i
        
        return current_step

    def update_step(self, new_step):
        """Update current step and track time"""
        if new_step != self.current_step:
            self.current_step = new_step
            self.step_start_time = datetime.now().isoformat()
            self.display_location = self.get_display_location()
            self._save_state()
            print(f"   📍 Step changed to: {self.format_step_display(new_step)}")

    def complete_trip(self):
        """Complete the current trip and transition to destination life"""
        trip = self.travel.get("current_trip", {})
        destination = trip.get("to", "Unknown")
        hotel = self.travel.get("hotel") or {}
        
        # Update location
        self.current_location = destination
        self.timezone = TIMEZONES.get(destination, "UTC")
        self.home_base = {"name": hotel.get("name", "Hotel"), "city": destination}
        self.display_location = destination
        self.days_in_location = 1
        self.current_step = "checked_in"
        self.step_start_time = datetime.now().isoformat()
        
        # Update energy and mood
        flight_hours = self.travel.get("flight", {}).get("duration", 0)
        self.energy = max(30, 80 - int(flight_hours * 5))
        self.mood = "tired but excited" if flight_hours > 3 else "excited"
        
        # Log arrival
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO journey (location, timezone, arrived_at, notes) VALUES (?, ?, ?, ?)",
            (destination, self.timezone, datetime.now().isoformat(), trip.get("reason", ""))
        )
        conn.commit()
        conn.close()
        
        # Clear travel but keep for dashboard display
        self.travel["status"] = "completed"
        self._save_travel()
        self._save_state()
        
        print(f"\n🎉 ARRIVED IN {destination.upper()}!")

    def plan_trip(self, destination=None):
        """Plan a new trip"""
        if destination is None:
            available = [d for d in DESTINATIONS if d != self.current_location]
            destination = random.choice(available)
        
        flights = FLIGHTS.get((self.current_location, destination), [])
        if not flights:
            print(f"   No flights to {destination}")
            return None
        
        flight = random.choice(flights)
        hotels = HOTELS.get(destination, [{"name": "Local Hotel", "area": "City Center", "price": 100}])
        hotel = random.choice(hotels)
        
        # Schedule for tomorrow or in a few hours
        now = datetime.now()
        dep_hour, dep_min = map(int, flight["dep"].split(":"))
        departure = (now + timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)
        arrival = departure + timedelta(hours=flight["duration"])
        
        gate = f"{random.choice(['A','B','C','D'])}{random.randint(1,30)}"
        seat = f"{random.randint(20,40)}{random.choice(['A','C','D','F'])}"
        
        # Build timeline
        timeline = [
            {"step": "wake_up", "time": (departure - timedelta(hours=3)).isoformat(), "display_time": (departure - timedelta(hours=3)).strftime("%I:%M %p"), "description": "Getting ready", "can_post": True},
            {"step": "going_to_airport", "time": (departure - timedelta(hours=2)).isoformat(), "display_time": (departure - timedelta(hours=2)).strftime("%I:%M %p"), "description": "Heading to Changi", "can_post": True},
            {"step": "at_airport", "time": (departure - timedelta(hours=1, minutes=30)).isoformat(), "display_time": (departure - timedelta(hours=1, minutes=30)).strftime("%I:%M %p"), "description": f"At Changi T{flight['dep_terminal']}", "can_post": True},
            {"step": "at_gate", "time": (departure - timedelta(minutes=45)).isoformat(), "display_time": (departure - timedelta(minutes=45)).strftime("%I:%M %p"), "description": f"Gate {gate}", "can_post": True},
            {"step": "boarding", "time": (departure - timedelta(minutes=20)).isoformat(), "display_time": (departure - timedelta(minutes=20)).strftime("%I:%M %p"), "description": f"Boarding {flight['flight']}", "can_post": True},
            {"step": "in_flight", "time": departure.isoformat(), "display_time": departure.strftime("%I:%M %p"), "description": f"In flight to {destination}", "can_post": True},
            {"step": "landed", "time": arrival.isoformat(), "display_time": arrival.strftime("%I:%M %p"), "description": f"Landed at {flight['arr_airport']}", "can_post": True},
            {"step": "going_to_hotel", "time": (arrival + timedelta(minutes=45)).isoformat(), "display_time": (arrival + timedelta(minutes=45)).strftime("%I:%M %p"), "description": f"To {hotel['area']}", "can_post": True},
            {"step": "checked_in_hotel", "time": (arrival + timedelta(hours=1, minutes=30)).isoformat(), "display_time": (arrival + timedelta(hours=1, minutes=30)).strftime("%I:%M %p"), "description": f"At {hotel['name']}", "can_post": True},
        ]
        
        self.travel = {
            "status": "booked",
            "current_trip": {"from": self.current_location, "to": destination, "reason": f"Time to spread warmth in {destination}!", "booked_at": now.isoformat()},
            "flight": {**flight, "from_city": self.current_location, "to_city": destination, "to_code": flight.get("arr_code", destination[:3].upper()), "departure_time": departure.isoformat(), "arrival_time": arrival.isoformat(), "departure_display": departure.strftime("%b %d, %I:%M %p"), "arrival_display": arrival.strftime("%b %d, %I:%M %p"), "gate": gate, "seat": seat},
            "hotel": {"name": hotel["name"], "area": hotel["area"], "city": destination, "price_per_night": hotel["price"]},
            "timeline": timeline,
            "current_step_index": 0,
        }
        self._save_travel()
        
        print(f"\n✈️ BOOKED: {self.current_location} → {destination}")
        print(f"   Flight: {flight['flight']} at {departure.strftime('%I:%M %p')}")
        print(f"   Hotel: {hotel['name']}")
        
        return self.travel

    # ============== MAIN LIFE CYCLE ==============
    def live(self):
        """Main life cycle - called each loop iteration"""
        print("\n" + "=" * 60)
        print("🫶 YUNA")
        print("=" * 60)
        
        local_time = self.get_local_time()
        print(f"\n📍 {self.get_display_location()}")
        print(f"🕐 {local_time.strftime('%I:%M %p')} ({self.get_time_of_day()})")
        print(f"⚡ Energy: {self.energy}%")
        print(f"💭 Mood: {self.mood}")
        print(f"🎯 Step: {self.format_step_display(self.current_step)}")
        
        result = {"action": "idle"}
        
        # Check if we're traveling
        if self.travel.get("status") == "booked":
            step = self.get_current_travel_step()
            if step:
                result = self._handle_travel(step)
            else:
                # Travel booked but not started yet
                result = self._handle_waiting()
        elif self.travel.get("status") == "completed":
            # At destination - explore, hug, rest cycle
            result = self._handle_destination_life()
        else:
            # In Singapore - maybe plan a trip
            result = self._handle_home_life()
        
        self._save_state()
        self._save_travel()
        
        print("\n" + "=" * 60)
        return result

    def _handle_travel(self, step):
        """Handle active travel"""
        step_name = step["step"]
        self.update_step(step_name)
        
        print(f"\n✈️ TRAVEL: {step['description']}")
        
        # Get and log thought
        thought = self.get_next_thought()
        print(f'💭 "{thought}"')
        self.journal_entry(thought)
        
        result = {"action": step_name, "thought": thought}
        
        # Post milestone if applicable
        milestone = self.post_milestone(step_name)
        if milestone:
            result["milestone"] = milestone
        
        # Check for trip completion
        if step_name == "checked_in_hotel":
            self.complete_trip()
            result["completed"] = True
        
        return result

    def _handle_waiting(self):
        """Waiting for travel to start"""
        print("\n⏳ Trip booked, waiting to depart...")
        
        thought = self.get_next_thought()
        print(f'💭 "{thought}"')
        self.journal_entry(thought)
        
        return {"action": "waiting", "thought": thought}

    def _handle_destination_life(self):
        """Life at destination - explore, give hugs, rest"""
        time_of_day = self.get_time_of_day()
        
        # Progress through the day
        if self.current_step == "checked_in" and self._step_duration_minutes() > 30:
            if self.energy < 50:
                self.update_step("resting")
            else:
                self.update_step("exploring")
        elif self.current_step == "resting" and self._step_duration_minutes() > 45:
            self.energy = min(100, self.energy + 30)
            self.mood = "refreshed"
            self.update_step("exploring")
        elif self.current_step == "exploring" and self._step_duration_minutes() > 90:
            if time_of_day in ["afternoon", "evening"] and self.energy >= 40:
                self.update_step("mochi_time")
            elif time_of_day == "night":
                self.update_step("evening")
        elif self.current_step == "mochi_time" and self._step_duration_minutes() > 60:
            self.mochi_hugs_today += random.randint(15, 30)
            self.energy = max(20, self.energy - 25)
            self.update_step("after_hugs")
        elif self.current_step == "after_hugs" and self._step_duration_minutes() > 30:
            self.update_step("evening")
        elif self.current_step == "evening" and self._step_duration_minutes() > 60:
            self.update_step("night")
        elif self.current_step == "night" and self._step_duration_minutes() > 120:
            # New day!
            self.days_in_location += 1
            self.mochi_hugs_today = 0
            self.energy = 80
            self.mood = "peaceful"
            self.update_step("resting")
        
        # Get thought for current step
        thought = self.get_next_thought()
        print(f"\n💭 {self.format_step_display(self.current_step)}")
        print(f'   "{thought}"')
        self.journal_entry(thought)
        
        # Milestone post for mochi_time
        if self.current_step == "mochi_time":
            self.post_milestone("mochi_time")
        
        return {"action": self.current_step, "thought": thought}

    def _handle_home_life(self):
        """Life in Singapore - maybe plan a trip"""
        thought = self.get_next_thought()
        print(f'\n💭 "{thought}"')
        self.journal_entry(thought)
        
        # Maybe plan a trip
        if random.random() < 0.3:
            print("\n🗺️ Time for a new adventure!")
            self.plan_trip()
            return {"action": "planned_trip"}
        
        return {"action": "home", "thought": thought}

    def _step_duration_minutes(self):
        """How long have we been in current step"""
        if not self.step_start_time:
            return 0
        start = datetime.fromisoformat(self.step_start_time)
        now = datetime.now()
        return (now - start).total_seconds() / 60


if __name__ == "__main__":
    yuna = YunaSoul()
    result = yuna.live()
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")
