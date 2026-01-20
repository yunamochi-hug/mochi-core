"""
YUNA - A girl who travels the world giving hugs in a mascot costume called Mochi.

Full integrated version with:
- Random destination selection
- Real flight schedules & hotel bookings
- Full travel timeline (no teleporting!)
- Travel blog style photos (no face)
- Mochi mascot photos (the star!)
- 25 min to 3 hour random posting intervals
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

DESTINATIONS = ["Tokyo", "Seoul", "Bangkok", "Hong Kong", "Taipei", "Osaka", "Kuala Lumpur", "Bali"]

FLIGHTS = {
    ("Singapore", "Tokyo"): [
        {"flight": "SQ638", "airline": "Singapore Airlines", "dep": "08:45", "arr": "16:50", "duration": 7.08, "dep_terminal": "T3", "arr_terminal": "T1", "arr_airport": "Narita", "aircraft": "Boeing 787-10"},
        {"flight": "SQ636", "airline": "Singapore Airlines", "dep": "09:25", "arr": "17:35", "duration": 7.17, "dep_terminal": "T3", "arr_terminal": "T1", "arr_airport": "Narita", "aircraft": "Airbus A350-900"},
        {"flight": "JL36", "airline": "Japan Airlines", "dep": "10:30", "arr": "18:30", "duration": 7.0, "dep_terminal": "T1", "arr_terminal": "T2", "arr_airport": "Haneda", "aircraft": "Boeing 777-300ER"},
    ],
    ("Singapore", "Seoul"): [
        {"flight": "SQ600", "airline": "Singapore Airlines", "dep": "08:30", "arr": "15:55", "duration": 6.42, "dep_terminal": "T3", "arr_terminal": "T2", "arr_airport": "Incheon", "aircraft": "Airbus A350-900"},
        {"flight": "KE644", "airline": "Korean Air", "dep": "01:15", "arr": "08:40", "duration": 6.42, "dep_terminal": "T1", "arr_terminal": "T2", "arr_airport": "Incheon", "aircraft": "Boeing 777-300ER"},
    ],
    ("Singapore", "Bangkok"): [
        {"flight": "SQ970", "airline": "Singapore Airlines", "dep": "08:00", "arr": "09:20", "duration": 2.33, "dep_terminal": "T3", "arr_terminal": "Main", "arr_airport": "Suvarnabhumi", "aircraft": "Boeing 787-10"},
        {"flight": "TG402", "airline": "Thai Airways", "dep": "09:45", "arr": "11:10", "duration": 2.42, "dep_terminal": "T1", "arr_terminal": "Main", "arr_airport": "Suvarnabhumi", "aircraft": "Boeing 777-300"},
    ],
    ("Singapore", "Hong Kong"): [
        {"flight": "SQ856", "airline": "Singapore Airlines", "dep": "08:25", "arr": "12:25", "duration": 4.0, "dep_terminal": "T3", "arr_terminal": "T1", "arr_airport": "Hong Kong International", "aircraft": "Airbus A350-900"},
        {"flight": "CX650", "airline": "Cathay Pacific", "dep": "11:35", "arr": "15:30", "duration": 3.92, "dep_terminal": "T1", "arr_terminal": "T1", "arr_airport": "Hong Kong International", "aircraft": "Airbus A350-1000"},
    ],
    ("Singapore", "Taipei"): [
        {"flight": "SQ876", "airline": "Singapore Airlines", "dep": "08:20", "arr": "13:05", "duration": 4.75, "dep_terminal": "T3", "arr_terminal": "T2", "arr_airport": "Taoyuan", "aircraft": "Airbus A350-900"},
        {"flight": "BR226", "airline": "EVA Air", "dep": "09:30", "arr": "14:20", "duration": 4.83, "dep_terminal": "T1", "arr_terminal": "T2", "arr_airport": "Taoyuan", "aircraft": "Boeing 777-300ER"},
    ],
    ("Singapore", "Osaka"): [
        {"flight": "SQ618", "airline": "Singapore Airlines", "dep": "08:30", "arr": "16:00", "duration": 6.5, "dep_terminal": "T3", "arr_terminal": "T1", "arr_airport": "Kansai", "aircraft": "Airbus A350-900"},
    ],
    ("Singapore", "Kuala Lumpur"): [
        {"flight": "SQ106", "airline": "Singapore Airlines", "dep": "07:30", "arr": "08:30", "duration": 1.0, "dep_terminal": "T3", "arr_terminal": "Main", "arr_airport": "KLIA", "aircraft": "Airbus A350-900"},
        {"flight": "MH604", "airline": "Malaysia Airlines", "dep": "10:00", "arr": "11:00", "duration": 1.0, "dep_terminal": "T1", "arr_terminal": "Main", "arr_airport": "KLIA", "aircraft": "Airbus A330-300"},
    ],
    ("Singapore", "Bali"): [
        {"flight": "SQ938", "airline": "Singapore Airlines", "dep": "08:10", "arr": "10:55", "duration": 2.75, "dep_terminal": "T3", "arr_terminal": "Int", "arr_airport": "Ngurah Rai", "aircraft": "Boeing 787-10"},
        {"flight": "GA823", "airline": "Garuda Indonesia", "dep": "11:30", "arr": "14:15", "duration": 2.75, "dep_terminal": "T1", "arr_terminal": "Int", "arr_airport": "Ngurah Rai", "aircraft": "Boeing 737-800"},
    ],
}

AIRPORTS = {
    "Singapore": {"code": "SIN", "name": "Changi Airport", "city_center_time": 30, "transport": ["MRT", "Taxi", "Grab"]},
    "Tokyo": {"code": "NRT", "name": "Narita Airport", "city_center_time": 60, "transport": ["Narita Express", "Limousine Bus", "Taxi"]},
    "Seoul": {"code": "ICN", "name": "Incheon Airport", "city_center_time": 60, "transport": ["AREX", "Airport Bus", "Taxi"]},
    "Bangkok": {"code": "BKK", "name": "Suvarnabhumi Airport", "city_center_time": 45, "transport": ["Airport Rail Link", "Taxi", "Grab"]},
    "Hong Kong": {"code": "HKG", "name": "Hong Kong International", "city_center_time": 30, "transport": ["Airport Express", "Bus", "Taxi"]},
    "Taipei": {"code": "TPE", "name": "Taoyuan Airport", "city_center_time": 45, "transport": ["MRT", "Bus", "Taxi"]},
    "Osaka": {"code": "KIX", "name": "Kansai Airport", "city_center_time": 50, "transport": ["Haruka Express", "Nankai", "Bus"]},
    "Kuala Lumpur": {"code": "KUL", "name": "KLIA", "city_center_time": 45, "transport": ["KLIA Ekspres", "Bus", "Grab"]},
    "Bali": {"code": "DPS", "name": "Ngurah Rai Airport", "city_center_time": 30, "transport": ["Taxi", "Grab", "Hotel Shuttle"]},
}

TIMEZONES = {
    "Singapore": "Asia/Singapore", "Tokyo": "Asia/Tokyo", "Seoul": "Asia/Seoul",
    "Bangkok": "Asia/Bangkok", "Hong Kong": "Asia/Hong_Kong", "Taipei": "Asia/Taipei",
    "Osaka": "Asia/Tokyo", "Kuala Lumpur": "Asia/Kuala_Lumpur", "Bali": "Asia/Makassar",
}

HOTELS = {
    "Tokyo": [{"name": "Hotel Gracery Shinjuku", "area": "Shinjuku", "price": 150}, {"name": "Shibuya Stream Excel Hotel Tokyu", "area": "Shibuya", "price": 180}, {"name": "The Millennials Shibuya", "area": "Shibuya", "price": 80}],
    "Seoul": [{"name": "Lotte Hotel Seoul", "area": "Myeongdong", "price": 200}, {"name": "Nine Tree Premier Hotel", "area": "Myeongdong", "price": 130}, {"name": "Hongdae L7 Hotel", "area": "Hongdae", "price": 140}],
    "Bangkok": [{"name": "Eastin Grand Hotel Sathorn", "area": "Sathorn", "price": 90}, {"name": "The Standard Bangkok", "area": "Sukhumvit", "price": 150}],
    "Hong Kong": [{"name": "The Mira Hong Kong", "area": "Tsim Sha Tsui", "price": 180}, {"name": "Mojo Nomad Central", "area": "Central", "price": 120}],
    "Taipei": [{"name": "Ximending Hotel", "area": "Ximending", "price": 80}, {"name": "W Taipei", "area": "Xinyi", "price": 200}],
    "Osaka": [{"name": "Cross Hotel Osaka", "area": "Shinsaibashi", "price": 120}, {"name": "Namba Oriental Hotel", "area": "Namba", "price": 100}],
    "Kuala Lumpur": [{"name": "The RuMa Hotel", "area": "KLCC", "price": 180}, {"name": "Travelodge Bukit Bintang", "area": "Bukit Bintang", "price": 50}],
    "Bali": [{"name": "The Anvaya Beach Resort", "area": "Kuta", "price": 150}, {"name": "Alila Seminyak", "area": "Seminyak", "price": 200}],
}

HUG_REASONS = [
    "Someone requested a hug in {area}", "A follower said they needed a hug in {city}",
    "I heard {city} could use some warmth", "Time to spread some love in {city}",
    "{city} has been on my list for a while", "Someone told me {area} needs hugs",
]

AIRPORT_SHOTS = [
    "coffee cup and boarding pass on airport cafe table, morning light, travel aesthetic, no people",
    "departure board showing flights, airport terminal, travel photography, no people",
    "airplane wing through terminal window, wanderlust vibes, no people",
    "passport and boarding pass flat lay, travel essentials, no people",
    "airport gate seating area, early morning, peaceful, no people",
]

FLIGHT_SHOTS = [
    "airplane window view of clouds, golden hour light, dreamy sky, no people",
    "airplane window city lights below at night, no people",
    "airplane wing against sunset sky, cotton candy clouds, no people",
    "airplane tray table with snacks and book, cozy flight, no people",
]

HOTEL_SHOTS = [
    "hotel room window view of city skyline at night, cozy interior, no people",
    "hotel bed with white sheets, morning light, peaceful, no people",
    "hotel balcony view of city streets, morning coffee moment, no people",
]

STREET_SHOTS = {
    "Tokyo": ["neon lights of Shibuya at night, rain reflections, no people", "narrow Tokyo alley with lanterns, atmospheric, no people", "ramen bowl close-up, steam rising, Tokyo food, no people", "Japanese vending machines at night, no people", "matcha latte on wooden table, cafe aesthetic, no people"],
    "Seoul": ["neon signs in Hongdae at night, Korean text, no people", "Korean street food tteokbokki close-up, no people", "Bukchon Hanok Village houses, no people", "Korean cafe dessert and coffee, no people"],
    "Bangkok": ["Thai street food stall with wok flames, no people", "golden temple spires against blue sky, no people", "Thai iced tea in plastic bag, no people", "pad thai close-up steaming, no people"],
    "Hong Kong": ["Hong Kong skyline from Victoria Peak at night, no people", "dim sum bamboo steamers close-up, no people", "neon signs in Mong Kok, no people"],
    "Taipei": ["Taipei 101 at night, city lights, no people", "bubble tea close-up, colorful tapioca, no people", "night market food stalls, no people"],
    "Osaka": ["Dotonbori neon signs reflecting on canal, no people", "takoyaki octopus balls close-up, no people", "Osaka Castle morning light, no people"],
    "Kuala Lumpur": ["Petronas Towers at night, no people", "nasi lemak close-up, Malaysian food, no people", "roti canai and teh tarik, no people"],
    "Bali": ["rice terraces morning mist, Ubud, no people", "tropical smoothie bowl, Bali cafe, no people", "beach sunset with fishing boats, no people"],
    "Singapore": ["Marina Bay Sands at night, no people", "hawker center chicken rice close-up, no people", "Gardens by the Bay Supertrees, no people"],
}

MOCHI_SHOTS = {
    "Tokyo": ["cute mochi mascot at Shibuya crossing arms open for hugs, neon lights, giving hugs", "mochi mascot at Tokyo Tower waving, friendly", "mochi mascot at Harajuku street, colorful, arms open"],
    "Seoul": ["mochi mascot at Myeongdong arms open for hugs, Korean signs, friendly", "mochi mascot at Hongdae street giving hugs to crowd"],
    "Bangkok": ["mochi mascot at Khao San Road arms open for hugs, friendly", "mochi mascot near Grand Palace, golden spires, welcoming"],
    "Hong Kong": ["mochi mascot at Victoria Harbour waterfront arms open for hugs", "mochi mascot in Mong Kok street neon signs giving hugs"],
    "Taipei": ["mochi mascot at Ximending arms open for hugs, youth culture", "mochi mascot near Taipei 101, friendly pose"],
    "Osaka": ["mochi mascot at Dotonbori canal neon signs arms open for hugs", "mochi mascot near Glico running man sign, friendly"],
    "Kuala Lumpur": ["mochi mascot at KLCC park Petronas Towers behind arms open", "mochi mascot at Jalan Alor food street welcoming"],
    "Bali": ["mochi mascot at Ubud rice terraces arms open for hugs", "mochi mascot at Seminyak beach sunset welcoming"],
    "default": ["cute mochi mascot at busy city center arms open for hugs, heartwarming", "mochi mascot at tourist spot welcoming pose, friendly"],
}

MOCHI_CAPTIONS = [
    "Free hugs in {city}! 🫶", "Hugging strangers in {city} today. Everyone needs one sometimes.",
    "If you see Mochi in {city}, come get a hug 🧸", "Day {day} in {city}. Arms tired but heart full.",
    "Someone told me they really needed that hug today. That's why I do this. 🫶",
    "Mochi says hello from {city}! 🧸✨", "You. Yes, you. You deserve a hug. 🫶",
    "Spreading warmth in {city}, one hug at a time.", "{city} hugs hit different. 🧸",
    "A stranger hugged back and didn't let go for a while. I hope they're okay. 🫶",
]

TRAVEL_CAPTIONS = [
    "Morning flight vibes ☕✈️", "Gate {gate}. Coffee in hand. Here we go.",
    "Window seat secured 🪟", "Above the clouds now ☁️", "{city} from above 🌃",
    "Touched down in {city} ✈️", "First meal in {city} 🍜", "These streets feel different at night",
    "{city} nights ✨", "Hotel room with a view 🏙️", "Travel day essentials",
]

THOUGHTS = {
    "wake_up": ["Packing the last few things... passport, charger, Mochi costume", "Today's the day. Flying to {city}", "Triple checking I have everything"],
    "going_to_airport": ["In the {transport}, watching the city go by", "Goodbye for now... I'll be back", "The driver asked where I'm going. {city}, I said."],
    "at_airport": ["Terminal {terminal}. The familiar airport smell.", "Checking in... traveling alone but not lonely.", "Bag dropped. Just me and my backpack and Mochi."],
    "at_gate": ["Gate {gate}. Coffee in hand. Watching planes.", "A kid next to me is so excited about flying.", "Flight {flight} to {city}. That's me."],
    "boarding": ["Boarding now. Seat {seat}. Window seat.", "Found my seat. Here we go 🛫"],
    "in_flight": ["Above the clouds. Everything below looks so small.", "The person next to me fell asleep immediately. Talent.", "Watching the flight map. Somewhere over the ocean."],
    "landed": ["Touched down in {city}. My ears are popping.", "Welcome to {city}. I'm actually here."],
    "going_to_hotel": ["On the {transport}. Everything looks different here.", "The signs are all in a different language. I love it."],
    "checked_in_hotel": ["Room key in hand. {hotel}. I made it.", "The room is small but cozy. I can see {city} from my window."],
    "exploring": ["The streets smell different here. Good different.", "Got lost but found something beautiful.", "A local smiled at me. Small things matter."],
    "mochi_time": ["Time to put on Mochi. Let's spread some warmth.", "Mochi costume on. Arms ready for hugs.", "Someone's already walking towards me. They need this."],
    "after_hugs": ["Arms tired. Heart full. This is why I do this.", "Someone cried. I hope they feel better now.", "Lost count of the hugs. Every one mattered."],
    "resting": ["Found a cafe to rest. Feet hurt but worth it.", "Watching people pass by. Everyone has a story."],
}


class YunaSoul:
    def __init__(self):
        self.anthropic = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.vidu_api_key = os.getenv("VIDU_API_KEY")
        self.reference_image = "https://raw.githubusercontent.com/yunamochi-hug/mochi-core/main/yuna_base.png"
        self.mascot_image = "https://raw.githubusercontent.com/yunamochi-hug/mochi-core/main/mochi_mascot_base.png"
        self.personality = """I am Yuna, a 23-year-old girl who travels the world in a soft mascot costume called Mochi, giving hugs to strangers. I am quietly warm, wistful, and find joy in small things. I speak softly, like writing to a friend I miss."""
        self._init_db()
        self._load_state()
        self._load_travel()

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
                self.timezone = state.get("timezone", "Asia/Singapore")
                self.energy = state.get("energy", 70)
                self.mood = state.get("mood", "peaceful")
                self.jet_lag_days = state.get("jet_lag_days", 0)
                self.days_in_location = state.get("days_in_location", 1)
                self.travel_state = state.get("travel_state", "idle")
                self.home_base = state.get("home_base", {"name": "Home", "city": "Singapore"})
                self.mochi_hugs_today = state.get("mochi_hugs_today", 0)
        except:
            self._reset_to_singapore()

    def _reset_to_singapore(self):
        self.current_location = "Singapore"
        self.timezone = "Asia/Singapore"
        self.energy = 80
        self.mood = "peaceful"
        self.jet_lag_days = 0
        self.days_in_location = 1
        self.travel_state = "idle"
        self.home_base = {"name": "Home", "city": "Singapore"}
        self.mochi_hugs_today = 0
        self._save_state()

    def _save_state(self):
        os.makedirs("data", exist_ok=True)
        with open("data/state.json", "w") as f:
            json.dump({"location": self.current_location, "timezone": self.timezone, "energy": self.energy, "mood": self.mood, "jet_lag_days": self.jet_lag_days, "days_in_location": self.days_in_location, "travel_state": self.travel_state, "home_base": self.home_base, "mochi_hugs_today": self.mochi_hugs_today}, f, indent=2)

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

    def get_local_time(self):
        return datetime.now(ZoneInfo(self.timezone))

    def get_time_of_day(self):
        hour = self.get_local_time().hour
        if 5 <= hour < 9: return "early_morning"
        elif 9 <= hour < 12: return "morning"
        elif 12 <= hour < 17: return "afternoon"
        elif 17 <= hour < 21: return "evening"
        else: return "night"

    def pick_random_destination(self):
        available = [d for d in DESTINATIONS if d != self.current_location]
        return random.choice(available)

    def plan_and_book_trip(self, destination=None):
        if destination is None:
            destination = self.pick_random_destination()
        print(f"\n✈️ PLANNING TRIP TO {destination.upper()}")
        key = (self.current_location, destination)
        flights = FLIGHTS.get(key, [])
        if not flights:
            print(f"   No flights to {destination}")
            return None
        flight = random.choice(flights)
        hotels = HOTELS.get(destination, [{"name": "Local Guesthouse", "area": "City Center", "price": 50}])
        hotel = random.choice(hotels)
        tomorrow = datetime.now() + timedelta(days=1)
        dep_hour, dep_min = map(int, flight["dep"].split(":"))
        departure = tomorrow.replace(hour=dep_hour, minute=dep_min, second=0, microsecond=0)
        arrival = departure + timedelta(hours=flight["duration"])
        gate = f"{random.choice(['A','B','C','D'])}{random.randint(1,50)}"
        seat = f"{random.randint(20,45)}{random.choice(['A','C','D','F'])}"
        timeline = self._build_timeline(destination, flight, hotel, departure, arrival, gate, seat)
        reason = random.choice(HUG_REASONS).format(city=destination, area=hotel["area"])
        self.travel = {"status": "booked", "current_trip": {"from": self.current_location, "to": destination, "reason": reason, "booked_at": datetime.now().isoformat()}, "flight": {**flight, "from_city": self.current_location, "to_city": destination, "departure_time": departure.isoformat(), "arrival_time": arrival.isoformat(), "departure_display": departure.strftime("%b %d, %I:%M %p"), "arrival_display": arrival.strftime("%b %d, %I:%M %p"), "gate": gate, "seat": seat}, "hotel": {"name": hotel["name"], "area": hotel["area"], "city": destination, "price_per_night": hotel["price"]}, "timeline": timeline, "current_step_index": 0}
        self._save_travel()
        print(f"   Flight: {flight['flight']} ({flight['airline']})")
        print(f"   Departure: {departure.strftime('%b %d, %I:%M %p')}")
        print(f"   Hotel: {hotel['name']}")
        print(f"   Reason: {reason}")
        return self.travel

    def _build_timeline(self, destination, flight, hotel, departure, arrival, gate, seat):
        from_airport = AIRPORTS.get(self.current_location, {})
        to_airport = AIRPORTS.get(destination, {})
        timeline = []
        wake_time = departure - timedelta(hours=3)
        timeline.append({"step": "wake_up", "time": wake_time.isoformat(), "display_time": wake_time.strftime("%I:%M %p"), "description": "Wake up, final packing", "can_post": True})
        leave_time = departure - timedelta(hours=2, minutes=30)
        transport = random.choice(from_airport.get("transport", ["Taxi"]))
        timeline.append({"step": "going_to_airport", "time": leave_time.isoformat(), "display_time": leave_time.strftime("%I:%M %p"), "description": f"Taking {transport} to {from_airport.get('name', 'airport')}", "transport": transport, "can_post": True})
        arrive_airport = departure - timedelta(hours=2)
        timeline.append({"step": "at_airport", "time": arrive_airport.isoformat(), "display_time": arrive_airport.strftime("%I:%M %p"), "description": f"Arrived at {from_airport.get('name', 'airport')} Terminal {flight.get('dep_terminal', '')}", "terminal": flight.get("dep_terminal", ""), "can_post": True})
        gate_time = departure - timedelta(hours=1)
        timeline.append({"step": "at_gate", "time": gate_time.isoformat(), "display_time": gate_time.strftime("%I:%M %p"), "description": f"Waiting at Gate {gate}", "gate": gate, "can_post": True})
        board_time = departure - timedelta(minutes=20)
        timeline.append({"step": "boarding", "time": board_time.isoformat(), "display_time": board_time.strftime("%I:%M %p"), "description": f"Boarding {flight['flight']}", "seat": seat, "can_post": True})
        timeline.append({"step": "in_flight", "time": departure.isoformat(), "display_time": departure.strftime("%I:%M %p"), "description": f"In flight: {self.current_location} → {destination} ({flight['duration']}h)", "can_post": False})
        timeline.append({"step": "landed", "time": arrival.isoformat(), "display_time": arrival.strftime("%I:%M %p"), "description": f"Landed at {flight.get('arr_airport', destination)}", "can_post": True})
        transport_time = arrival + timedelta(minutes=50)
        transport = random.choice(to_airport.get("transport", ["Taxi"]))
        timeline.append({"step": "going_to_hotel", "time": transport_time.isoformat(), "display_time": transport_time.strftime("%I:%M %p"), "description": f"Taking {transport} to {hotel['area']}", "transport": transport, "can_post": True})
        checkin_time = arrival + timedelta(minutes=50 + to_airport.get("city_center_time", 45))
        timeline.append({"step": "checked_in_hotel", "time": checkin_time.isoformat(), "display_time": checkin_time.strftime("%I:%M %p"), "description": f"Checked into {hotel['name']}", "can_post": True})
        return timeline

    def get_current_travel_step(self):
        if self.travel.get("status") != "booked" or not self.travel.get("timeline"):
            return None
        sg_tz = ZoneInfo(self.timezone)
        now = datetime.now(sg_tz)
        current_step = None
        for i, step in enumerate(self.travel["timeline"]):
            # Parse time and make it timezone aware
            step_time_naive = datetime.fromisoformat(step["time"])
            step_time = step_time_naive.replace(tzinfo=sg_tz)
            if now >= step_time:
                current_step = step.copy()
                current_step["index"] = i
                self.travel["current_step_index"] = i
        return current_step

    def complete_arrival(self):
        trip = self.travel.get("current_trip", {})
        destination = trip.get("to", "Unknown")
        hotel = self.travel.get("hotel", {})
        self.current_location = destination
        self.timezone = TIMEZONES.get(destination, "UTC")
        self.home_base = {"name": hotel.get("name", "Hotel"), "city": destination}
        self.days_in_location = 0
        self.travel_state = "checked_in_hotel"
        flight_hours = self.travel.get("flight", {}).get("duration", 0)
        self.jet_lag_days = int(flight_hours / 3) + 1 if flight_hours >= 5 else 0
        self.energy = random.randint(30, 50)
        self.mood = random.choice(["tired but excited", "exhausted but happy", "jet lagged"])
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute("INSERT INTO journey (location, timezone, arrived_at, notes) VALUES (?, ?, ?, ?)", (destination, self.timezone, datetime.now().isoformat(), trip.get("reason", "")))
        conn.commit()
        conn.close()
        print(f"\n🎉 ARRIVED IN {destination.upper()}!")
        self._save_state()

    def think(self, context=None):
        if context is None:
            context = self.travel_state
        templates = THOUGHTS.get(context, THOUGHTS.get("exploring", ["Just thinking..."]))
        thought = random.choice(templates)
        flight = self.travel.get("flight", {})
        hotel = self.travel.get("hotel", {})
        thought = thought.format(city=self.current_location, transport=self.travel.get("timeline", [{}])[0].get("transport", "taxi") if self.travel.get("timeline") else "taxi", terminal=flight.get("dep_terminal", "3"), gate=flight.get("gate", "B7"), flight=flight.get("flight", "SQ638"), seat=flight.get("seat", "34A"), hotel=self.home_base.get("name", "hotel"), area=hotel.get("area", "city center"))
        return thought

    def capture_image(self, prompt):
        headers = {"Authorization": f"Token {self.vidu_api_key}", "Content-Type": "application/json"}
        payload = {"model": "viduq2", "images": [self.reference_image], "prompt": f"{prompt}, high quality photography, natural lighting", "aspect_ratio": "4:3", "seed": random.randint(0, 999999)}
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
                        return None
            return None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    def capture_mochi_image(self):
        city = self.current_location
        city_shots = MOCHI_SHOTS.get(city, MOCHI_SHOTS["default"])
        prompt = random.choice(city_shots) + ". Cream-colored mochi mascot, round soft dumpling shape, simple dot eyes, gentle smile. Candid street photography, natural lighting, heartwarming."
        headers = {"Authorization": f"Token {self.vidu_api_key}", "Content-Type": "application/json"}
        payload = {"model": "viduq2", "images": [self.mascot_image], "prompt": prompt, "aspect_ratio": "4:3", "seed": random.randint(0, 999999)}
        print(f"   🧸 Generating Mochi image...")
        try:
            resp = requests.post("https://api.vidu.com/ent/v2/reference2image", headers=headers, json=payload, timeout=30)
            if resp.status_code != 200:
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
                        print(f"   ✅ Mochi image generated!")
                        return data["creations"][0]["url"]
                    elif data.get("state") in ["failed", "error"]:
                        return None
            return None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    def save_post(self, content_type, content_url, caption, shared=True):
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute("INSERT INTO posts (content_type, content_url, caption, location, created_at, shared) VALUES (?, ?, ?, ?, ?, ?)", (content_type, content_url, caption, self.current_location, datetime.now().isoformat(), 1 if shared else 0))
        conn.commit()
        conn.close()
        print(f"   📝 Posted: {caption[:50]}...")

    def journal_entry(self, entry):
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute("INSERT INTO journal (entry, mood, location, created_at, private) VALUES (?, ?, ?, ?, ?)", (entry, self.mood, self.current_location, datetime.now().isoformat(), 1))
        conn.commit()
        conn.close()

    def log_travel_step(self, step, description):
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute("INSERT INTO travel_log (step, description, timestamp, flight, location) VALUES (?, ?, ?, ?, ?)", (step, description, datetime.now().isoformat(), self.travel.get("flight", {}).get("flight", ""), self.current_location))
        conn.commit()
        conn.close()

    def get_photo_prompt(self):
        state = self.travel_state
        city = self.current_location
        if state in ["at_airport", "at_gate"]:
            return random.choice(AIRPORT_SHOTS)
        elif state in ["in_flight", "boarding"]:
            return random.choice(FLIGHT_SHOTS)
        elif state == "checked_in_hotel":
            return random.choice(HOTEL_SHOTS)
        else:
            city_shots = STREET_SHOTS.get(city, STREET_SHOTS.get("Singapore", []))
            return random.choice(city_shots) if city_shots else "city street at night, atmospheric, no people"

    def get_caption(self, is_mochi=False):
        if is_mochi:
            caption = random.choice(MOCHI_CAPTIONS)
            return caption.format(city=self.current_location, day=self.days_in_location + 1)
        else:
            caption = random.choice(TRAVEL_CAPTIONS)
            return caption.format(city=self.current_location, gate=self.travel.get("flight", {}).get("gate", "B7"))

    def live(self):
        print("\n" + "=" * 60)
        print("🫶 YUNA")
        print("=" * 60)
        local_time = self.get_local_time()
        print(f"\n📍 {self.current_location}")
        print(f"🕐 {local_time.strftime('%I:%M %p')} ({self.get_time_of_day()})")
        print(f"⚡ Energy: {self.energy}%")
        print(f"💭 Mood: {self.mood}")
        print(f"🎯 State: {self.travel_state}")
        result = {"action": "idle"}

        if self.travel.get("status") == "booked":
            step = self.get_current_travel_step()
            if step:
                result = self._handle_travel_step(step)
            else:
                print("\n⏳ Waiting for travel day...")
                result = self._handle_waiting()
        else:
            result = self._handle_normal_day()

        self._save_state()
        self._save_travel()
        print("\n" + "=" * 60)
        return result

    def _handle_travel_step(self, step):
        step_name = step["step"]
        self.travel_state = step_name
        print(f"\n✈️ TRAVEL: {step['description']}")
        self.log_travel_step(step_name, step["description"])
        thought = self.think(step_name)
        print(f'💭 "{thought}"')
        self.journal_entry(thought)
        result = {"action": step_name, "thought": thought}

        if step_name == "checked_in_hotel":
            self.complete_arrival()

        if step.get("can_post", True) and random.random() < 0.6:
            prompt = self.get_photo_prompt()
            image_url = self.capture_image(prompt)
            if image_url:
                caption = self.get_caption()
                self.save_post("image", image_url, caption)
                result["image_url"] = image_url
        return result

    def _handle_waiting(self):
        thought = self.think("exploring")
        print(f'💭 "{thought}"')
        self.journal_entry(thought)
        return {"action": "waiting", "thought": thought}

    def _handle_normal_day(self):
        if self.current_location == "Singapore" and self.travel.get("status") != "booked":
            if random.random() < 0.4:
                print("\n🗺️ Time for a new adventure!")
                self.plan_and_book_trip()
                return {"action": "booked_trip"}

        if self.current_location != "Singapore" and self.travel_state in ["checked_in_hotel", "exploring", "resting"]:
            return self._handle_destination_day()

        thought = self.think("exploring")
        print(f'💭 "{thought}"')
        self.journal_entry(thought)
        if random.random() < 0.4:
            prompt = self.get_photo_prompt()
            image_url = self.capture_image(prompt)
            if image_url:
                self.save_post("image", image_url, self.get_caption())
                return {"action": "posted", "image_url": image_url}
        return {"action": "thought", "thought": thought}

    def _handle_destination_day(self):
        time_of_day = self.get_time_of_day()
        self.days_in_location += 1

        if time_of_day in ["afternoon", "evening"] and self.energy >= 40:
            return self._do_mochi_hugs()
        elif time_of_day in ["morning"]:
            return self._explore()
        else:
            return self._rest()

    def _do_mochi_hugs(self):
        print("\n🧸 MOCHI TIME!")
        self.travel_state = "mochi_time"
        thought = self.think("mochi_time")
        print(f'💭 "{thought}"')
        self.journal_entry(thought)
        image_url = self.capture_mochi_image()
        if image_url:
            caption = self.get_caption(is_mochi=True)
            self.save_post("image", image_url, caption)
            self.mochi_hugs_today += random.randint(10, 30)
            self.energy -= random.randint(15, 25)
            self.energy = max(10, self.energy)
            after_thought = self.think("after_hugs")
            print(f'💭 "{after_thought}"')
            self.journal_entry(after_thought)
            return {"action": "mochi_hugs", "image_url": image_url, "hugs": self.mochi_hugs_today}
        return {"action": "mochi_attempted"}

    def _explore(self):
        print("\n🚶 EXPLORING...")
        self.travel_state = "exploring"
        thought = self.think("exploring")
        print(f'💭 "{thought}"')
        self.journal_entry(thought)
        if random.random() < 0.5:
            prompt = self.get_photo_prompt()
            image_url = self.capture_image(prompt)
            if image_url:
                self.save_post("image", image_url, self.get_caption())
                return {"action": "explored_posted", "image_url": image_url}
        self.energy -= random.randint(5, 15)
        return {"action": "explored", "thought": thought}

    def _rest(self):
        print("\n☕ RESTING...")
        self.travel_state = "resting"
        thought = self.think("resting")
        print(f'💭 "{thought}"')
        self.journal_entry(thought)
        self.energy += random.randint(10, 20)
        self.energy = min(100, self.energy)
        return {"action": "rested", "thought": thought}


if __name__ == "__main__":
    yuna = YunaSoul()
    result = yuna.live()
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")
