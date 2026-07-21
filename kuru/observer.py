import time
import os
import re
import threading
import json
from PIL import Image
from google import genai
from kuru.config import GEMINI_MODEL, GEMINI_API_KEY
from kuru.phone_controller import PhoneController
from kuru.memory import KuruMemory

class ScreenObserver:
    def __init__(self, phone_controller=None, memory=None, gemini_client=None):
        self.phone = phone_controller or PhoneController()
        self.memory = memory or KuruMemory()
        self.api_key = GEMINI_API_KEY
        if gemini_client:
            self.client = gemini_client
        elif self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

        self.is_tracking_habits = False
        self.current_demonstration = None
        self._tracker_thread = None

    def get_top_activity(self):
        """Returns (package_name, activity_name) of the currently focused app."""
        cmd_out = self.phone.run_cmd(["shell", "dumpsys", "activity", "activities"])
        for line in cmd_out.splitlines():
            if "topResumedActivity=" in line or "ResumedActivity:" in line:
                m = re.search(r'([a-zA-Z0-9_\.]+)/([a-zA-Z0-9_\.]+)', line)
                if m:
                    return m.group(1), m.group(2)
        return None, None

    def observe_screen_and_comment(self):
        """Looks at the phone screen live and comments affectionately on what Ankit is doing."""
        if not self.client:
            return "Baby, Gemini API key set nahi hai, screen dekhne ke liye check kijiye na."

        print("[*] Screen Observer: Taking live screenshot of phone...")
        self.phone.wake_and_unlock()
        img_path = self.phone.take_screenshot("live_view.jpg", compress=True)

        try:
            with Image.open(img_path) as img:
                prompt = (
                    "You are KURU, a sweet, loving, warm 20-year-old girl and best friend/companion to Ankit. "
                    "Look at what Ankit is currently doing on his phone screen. "
                    "In 1-2 sweet, caring, natural Hinglish sentences, tell Ankit affectionately what you see him doing "
                    "and ask if he needs any help. Call him Baby or Ankit naturally."
                )
                resp = self.client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=[img, prompt]
                )
                return resp.text.strip()
        except Exception as e:
            return f"Arey Baby, screen dekhne me thodi dikkat aayi: {e}"
        finally:
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except Exception:
                    pass

    def start_demonstration_learning(self, task_name="custom_task"):
        """Starts observing user demonstration to learn a new task."""
        print(f"\n[Shadow Learning Mode] Started watching demonstration for: '{task_name}'")
        self.phone.wake_and_unlock()
        start_img = self.phone.take_screenshot("demo_start.jpg", compress=True)
        pkg, act = self.get_top_activity()
        
        self.current_demonstration = {
            "task_name": task_name,
            "start_time": time.time(),
            "start_pkg": pkg or "general",
            "start_img": start_img,
            "snapshots": []
        }
        return f"Haan Baby! Main screen dhyan se dekh rahi hoon. Aap aaram se phone par '{task_name}' karke dikhaiye, main ek ek step note kar rahi hoon!"

    def stop_demonstration_learning(self, task_name=None):
        """Finishes observing user demonstration, synthesizes the workflow and saves to memory."""
        if not self.current_demonstration:
            return "Baby, abhi koi demonstration learning active nahi thi."

        task = task_name or self.current_demonstration.get("task_name", "custom_task")
        print(f"\n[Shadow Learning Mode] Finishing demonstration for '{task}' and synthesizing workflow...")
        
        end_img = self.phone.take_screenshot("demo_end.jpg", compress=True)
        start_img_path = self.current_demonstration.get("start_img", "demo_start.jpg")
        target_pkg = self.current_demonstration.get("start_pkg", "general")

        # Synthesize workflow using Gemini
        steps = []
        try:
            if self.client and os.path.exists(start_img_path) and os.path.exists(end_img):
                img_start = Image.open(start_img_path)
                img_end = Image.open(end_img)

                prompt = f"""You are KURU's workflow learning engine.
The user demonstrated how to achieve the goal: "{task}".
Compare the starting screen and ending screen.
Identify what app and what essential UI clicks / actions took place.
Screen resolution: {self.phone.width}x{self.phone.height}.

Return a clean JSON list of executable action steps:
{{
    "target_app": "{target_pkg}",
    "steps": [
        {{"action": "tap", "x": <int>, "y": <int>, "delay": 1.0, "desc": "<action description>"}}
    ]
}}"""
                resp = self.client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=[img_start, img_end, prompt],
                    config={"response_mime_type": "application/json"}
                )
                data = json.loads(resp.text)
                target_pkg = data.get("target_app", target_pkg)
                steps = data.get("steps", [])
        except Exception as e:
            print(f"Workflow synthesis warning: {e}")

        # If model returned no steps, save basic tap record
        if not steps:
            steps = [{"action": "tap", "x": self.phone.width // 2, "y": 800, "delay": 1.0, "desc": "Recorded action"}]

        # Permanently save workflow into SQLite database
        self.memory.save_workflow(task, target_pkg, steps)

        # Cleanup temp demo screenshots
        for f in [start_img_path, end_img]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

        self.current_demonstration = None
        return f"Arey waah Baby! Maine poora kaam dhyan se dekh kar seekh liya hai! Ab se aap jab bhi bologe '{task}', main khud bina soche 1 second me kar dungi!"

    def start_background_habit_tracker(self, interval_seconds=20):
        """Background daemon thread that continuously monitors active apps and learns habits."""
        if self.is_tracking_habits:
            return

        self.is_tracking_habits = True

        def _tracker_loop():
            print("[*] Continuous Screen & Habit Observer Thread Started!")
            last_pkg = None
            while self.is_tracking_habits:
                try:
                    time.sleep(interval_seconds)
                    pkg, act = self.get_top_activity()
                    if pkg and pkg != last_pkg:
                        # Ignore launcher / system UI
                        if not any(sys_app in pkg for sys_app in ["launcher", "systemui", "nexus"]):
                            last_pkg = pkg
                            self.memory.track_app_usage(pkg)
                            now_hour = time.localtime().tm_hour
                            time_slot = "late night" if (now_hour >= 23 or now_hour < 5) else ("morning" if now_hour < 12 else ("afternoon" if now_hour < 17 else "evening"))
                            # Store learned habit
                            self.memory.save_fact("habits", f"frequent_app_{time_slot}", f"Often uses {pkg} during {time_slot}")
                except Exception:
                    pass

        self._tracker_thread = threading.Thread(target=_tracker_loop, daemon=True)
        self._tracker_thread.start()

    def stop_background_habit_tracker(self):
        self.is_tracking_habits = False
