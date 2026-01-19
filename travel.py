"""
YUNA'S TRAVEL SYSTEM - Planning trips, booking flights, hotels
"""

import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import os

# Real flight durations (approximate hours)
FLIGHT_TIMES = {
    ("Singapore", "Tokyo"): 7,
    ("Singapore", "Hong Kong"): 4,
    ("Singapore", "Bangkok"): 2.5,
    ("Singapore", "Seoul"): 6.5,
    ("Singapore", "Taipei"): 4.5,
    ("Singapore", "Kuala Lumpur"): 1,
    ("Singapore", "Bali"): 2.5,
    ("Singapore", "Melbourne"): 8,
    ("Singapore", "London"): 13,
    ("Singapore", "Paris"): 13,
    ("Singapore", "New York"): 19,
    ("Tokyo", "Seoul"): 2.5,
    ("Tokyo", "Hong Kong"): 4,
    ("Tokyo", "Taipei"): 3,
    ("Tokyo", "Bangkok"): 6,
    ("Hong Kong", "Bangkok"): 3,
    ("Bangkok", "Bali"): 4,
    ("Seoul", "Taipei"): 2.5,
}

# Timezone mapping
CITY_TIMEZONES = {
    "Singapore": "Asia/Singapore",
    "Tokyo": "Asia/Tokyo",
    "Hong Kong": "Asia/Hong_Kong",
    "Bangkok": "Asia/Bangkok",
    "Seoul": "Asia/Seoul",
    "Taipei": "Asia/Taipei",
    "Kuala Lumpur": "Asia/Kuala_Lumpur",
    "Bali": "Asia/Makassar",
    "Melbourne": "Australia/Melbourne",
    "London": "Europe/London",
    "Paris": "Europe/Paris",
    "New York": "America/New_York",
}

class TravelPlanner:
    def __init__(self, state_file="data/travel.json"):
        self.state_file = state_file
        self.load_state()
    
    def load_state(self):
        try:
            with open(self.state_file, "r") as f:
                self.state = json.load(f)
        except:
            self.state = {
                "current_city": "Singapore",
                "home_base": None,
                "planned_trip": None,
                "flight_booked": None,
                "hotel_booked": None,
                "traveling": False,
                "flight_departure": None,
                "flight_arrival": None
            }
    
    def save_state(self):
        os.makedirs("data", exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def get_flight_duration(self, from_city, to_city):
        key = (from_city, to_city)
        if key in FLIGHT_TIMES:
            return FLIGHT_TIMES[key]
        key = (to_city, from_city)
        if key in FLIGHT_TIMES:
            return FLIGHT_TIMES[key]
        return random.randint(4, 12)
    
    def get_timezone(self, city):
        return CITY_TIMEZONES.get(city, "UTC")
    
    def set_home_base(self, hotel_name, city):
        self.state["home_base"] = {
            "name": hotel_name,
            "city": city,
            "checked_in": datetime.now().isoformat()
        }
        self.state["current_city"] = city
        self.save_state()
    
    def plan_trip(self, destination, reason="exploring"):
        current = self.state.get("current_city", "Singapore")
        duration = self.get_flight_duration(current, destination)
        timezone = self.get_timezone(destination)
        
        self.state["planned_trip"] = {
            "from": current,
            "to": destination,
            "flight_hours": duration,
            "timezone": timezone,
            "reason": reason,
            "planned_at": datetime.now().isoformat()
        }
        self.save_state()
        
        return {
            "from": current,
            "to": destination,
            "flight_hours": duration
        }
    
    def book_flight(self, departure_time=None):
        if not self.state.get("planned_trip"):
            return {"error": "No trip planned"}
        
        trip = self.state["planned_trip"]
        
        if departure_time is None:
            tomorrow = datetime.now() + timedelta(days=1)
            departure_time = tomorrow.replace(hour=random.choice([8, 10, 14, 16]), minute=0)
        
        arrival_time = departure_time + timedelta(hours=trip["flight_hours"])
        
        self.state["flight_booked"] = {
            "from": trip["from"],
            "to": trip["to"],
            "departure": departure_time.isoformat(),
            "arrival": arrival_time.isoformat(),
            "flight_number": f"SQ{random.randint(100, 999)}",
            "booked_at": datetime.now().isoformat()
        }
        self.save_state()
        
        return self.state["flight_booked"]
    
    def book_hotel(self, hotel_name=None):
        if not self.state.get("planned_trip"):
            return {"error": "No trip planned"}
        
        trip = self.state["planned_trip"]
        destination = trip["to"]
        
        if hotel_name is None:
            prefixes = ["The", "Hotel", ""]
            names = ["Grand", "Central", "Garden", "City", "Park", "Harbor", "Sakura", "Lotus"]
            suffixes = ["Inn", "Hotel", "Suites", "Stay", "House", "Hostel"]
            hotel_name = f"{random.choice(prefixes)} {random.choice(names)} {random.choice(suffixes)}".strip()
        
        self.state["hotel_booked"] = {
            "name": hotel_name,
            "city": destination,
            "booked_at": datetime.now().isoformat()
        }
        self.save_state()
        
        return self.state["hotel_booked"]
    
    def start_travel(self):
        if not self.state.get("flight_booked"):
            return {"error": "No flight booked"}
        
        self.state["traveling"] = True
        self.state["flight_departure"] = datetime.now().isoformat()
        self.save_state()
        return {"status": "traveling"}
    
    def complete_travel(self):
        if not self.state.get("traveling"):
            return {"error": "Not traveling"}
        
        trip = self.state["planned_trip"]
        
        self.state["current_city"] = trip["to"]
        self.state["traveling"] = False
        self.state["flight_arrival"] = datetime.now().isoformat()
        
        if self.state.get("hotel_booked"):
            self.state["home_base"] = self.state["hotel_booked"]
        
        self.state["planned_trip"] = None
        self.state["flight_booked"] = None
        self.state["hotel_booked"] = None
        
        self.save_state()
        
        return {"arrived": trip["to"], "hotel": self.state.get("home_base", {}).get("name")}
    
    def is_traveling(self):
        return self.state.get("traveling", False)
    
    def get_home_base(self):
        return self.state.get("home_base")
    
    def get_current_city(self):
        return self.state.get("current_city", "Singapore")
