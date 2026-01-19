import anthropic
import requests
import os
import time
import json
import sqlite3
import random
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class MochiSoul:
    def __init__(self):
        self.anthropic = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.vidu_api_key = os.getenv("VIDU_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.name = "Yuna"
        self.mascot = "Mochi"
        self.birthday = "January 18, 2026"
        self.current_location = self._load_state().get("location", "Singapore")
        self.current_mood = self._load_state().get("mood", "peaceful")
        self.reference_image = "https://raw.githubusercontent.com/yunamochi-hug/mochi-core/main/yuna_base.png"
        self.personality = """I am Yuna, a 23-year-old girl who travels the world in a soft mascot costume called Mochi, giving hugs to strangers.
        I am quietly warm, wistful, and find joy in small things. I speak softly, like writing to a friend I miss."""
        self._init_db()
    
    def _load_state(self):
        try:
            with open("data/state.json", "r") as f:
                return json.load(f)
        except:
            return {"location": "Singapore", "mood": "peaceful"}
    
    def _save_state(self):
        os.makedirs("data", exist_ok=True)
        with open("data/state.json", "w") as f:
            json.dump({"location": self.current_location, "mood": self.current_mood}, f)
    
    def _init_db(self):
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect("data/mochi.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS journey (id INTEGER PRIMARY KEY, location TEXT, arrived_at TEXT, notes TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS hug_requests (id INTEGER PRIMARY KEY, name TEXT, email TEXT, city TEXT, country TEXT, message TEXT, requested_at TEXT, status TEXT DEFAULT 'waiting')''')
        c.execute('''CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, image_url TEXT, caption TEXT, location TEXT, created_at TEXT)''')
        conn.commit()
        conn.close()
    
    def think(self, prompt):
        message = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=f"You are Yuna. {self.personality} Current location: {self.current_location}. Be soft, warm, concise.",
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    def decide_what_to_photograph(self):
        prompt = """What do you want to photograph right now? Respond in JSON only:
        {"scene": "description", "angle": "selfie/portrait/wide/close-up", "mood": "feeling", "caption_idea": "caption"}"""
        response = self.think(prompt)
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {"scene": "quiet cafe moment", "angle": "portrait", "mood": "peaceful", "caption_idea": "Small moments matter."}
    
    def get_place_info(self, place_name):
        if not self.google_api_key:
            return None
        url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        params = {"input": place_name, "inputtype": "textquery", "fields": "name,formatted_address,geometry,photos,types,rating", "key": self.google_api_key}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("candidates"):
                return data["candidates"][0]
        return None
    
    def get_nearby_places(self, location, place_type="tourist_attraction", radius=5000):
        if not self.google_api_key:
            return []
        place_info = self.get_place_info(location)
        if not place_info or "geometry" not in place_info:
            return []
        lat = place_info["geometry"]["location"]["lat"]
        lng = place_info["geometry"]["location"]["lng"]
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {"location": f"{lat},{lng}", "radius": radius, "type": place_type, "key": self.google_api_key}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get("results", [])[:10]
        return []
    
    def see(self, scene_description=None):
        if not scene_description:
            decision = self.decide_what_to_photograph()
            scene_description = decision["scene"]
            print(f"  💭 Mood: {decision['mood']}, Angle: {decision['angle']}")
        
        headers = {"Authorization": f"Token {self.vidu_api_key}", "Content-Type": "application/json"}
        prompt = f"""Same young Asian woman from reference image, short black messy hair, natural look.
        {scene_description}.
        Photograph taken on iPhone, candid moment, natural lighting, realistic skin, 
        no text, no watermarks, no writing, no logos, no numbers, no asian characters, documentary style."""
        
        payload = {"model": "viduq2", "images": [self.reference_image], "prompt": prompt, "aspect_ratio": "4:3", "seed": random.randint(0, 999999)}
        
        print("  📸 Capturing moment...")
        resp = requests.post("https://api.vidu.com/ent/v2/reference2image", headers=headers, json=payload)
        if resp.status_code != 200:
            return f"Error: {resp.status_code}"
        task_id = resp.json().get("task_id")
        
        for i in range(80):
            time.sleep(3)
            if i % 15 == 0 and i > 0:
                print(f"  ⏳ Still working... ({i*3}s)")
            result = requests.get(f"https://api.vidu.com/ent/v2/tasks/{task_id}/creations", headers=headers)
            if result.status_code == 200:
                data = result.json()
                if data.get("state") == "success":
                    return data["creations"][0]["url"]
                elif data.get("state") in ["failed", "error"]:
                    return f"Failed: {data}"
        return "Timeout"
    
    def wander(self):
        print(f"\n🚶‍♀️ Yuna is wandering in {self.current_location}...")
        decision = self.decide_what_to_photograph()
        print(f"💭 Mood: {decision['mood']}")
        print(f"🎬 Scene: {decision['scene'][:80]}...")
        image_url = self.see(decision['scene'])
        caption = self.think(f"Write a short caption for: {decision['caption_idea']}. Under 50 words, no hashtags.")
        print(f"\n🖼️  IMAGE: {image_url}")
        print(f"✍️  CAPTION: {caption}")
        return {"image": image_url, "caption": caption}
    
    def travel_to(self, destination):
        old = self.current_location
        info = self.get_place_info(destination)
        self.current_location = info.get("name", destination) if info else destination
        self._save_state()
        print(f"✈️ Traveled from {old} to {self.current_location}")
        return self.current_location

if __name__ == "__main__":
    print("🫰 YUNA WAKES UP")
    yuna = MochiSoul()
    print(f"📍 Location: {yuna.current_location}")
    yuna.wander()
