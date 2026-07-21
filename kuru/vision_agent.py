import json
import os
from PIL import Image
from google import genai
from google.genai import types
from kuru.config import GEMINI_MODEL

class VisionAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def set_api_key(self, api_key):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    def plan_next_action(self, image_path, goal, ui_elements=None, screen_width=1080, screen_height=2400):
        if not self.client:
            return {"action": "error", "message": "Gemini API Key missing"}

        img = Image.open(image_path)
        elements_context = ""
        if ui_elements:
            elem_summary = []
            for e in ui_elements[:25]:
                txt = e.get("text") or e.get("desc")
                cx, cy = e.get("center", (0, 0))
                if txt:
                    elem_summary.append(f"- '{txt}' at ({cx}, {cy})")
            if elem_summary:
                elements_context = "\nInteractive elements detected on screen:\n" + "\n".join(elem_summary)

        prompt = f"""Screen size: {screen_width}x{screen_height}.
Goal: "{goal}"
{elements_context}

Look at the phone screenshot and interactive elements. Decide the next action to achieve the goal.
Rules:
1. If you are on the home screen and the required app is not visible, RETURN: {{"action": "swipe_up"}} to open the app drawer! NEVER give up or return "done" just because an app is not on the home screen.
2. If inside the app drawer, tap the app icon or tap the search bar to find it.
3. Return {{"action": "done", "reason": "<sweet short Hindi summary of success>"}} ONLY when the user's ultimate goal has ACTUALLY been achieved!

Respond ONLY in JSON:
{{"action": "tap", "x": <int>, "y": <int>}}
OR {{"action": "type", "text": "<text>"}}
OR {{"action": "swipe_up"}}
OR {{"action": "scroll_down"}}
OR {{"action": "scroll_up"}}
OR {{"action": "key", "key": "back"|"home"|"enter"}}
OR {{"action": "done", "reason": "<short summary>"}}"""

        try:
            resp = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[img, prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(resp.text)
        except Exception as e:
            return {"action": "done", "reason": f"Completed ({e})"}
