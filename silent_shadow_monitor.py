import time
import os
import sys
import re
import datetime
import sqlite3
import json

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from google import genai
from kuru.config import GEMINI_MODEL, GEMINI_API_KEY
from kuru.phone_controller import PhoneController
from kuru.memory import KuruMemory

class SilentShadowMonitor:
    def __init__(self):
        self.phone = PhoneController()
        self.memory = KuruMemory()
        self.api_key = GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        
        self.log_file = "shadow_monitor.log"
        self.is_running = True
        
        # State tracking
        self.last_pkg = None
        self.last_activity = None
        self.app_start_time = time.time()
        self.session_actions = []

    def log(self, text):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{now_str}] {text}"
        print(entry)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception:
            pass

    def is_screen_awake(self):
        """Checks if phone screen is actively turned on."""
        out = self.phone.run_cmd(["shell", "dumpsys", "power"])
        return "mWakefulness=Awake" in str(out)

    def get_focused_window(self):
        """Returns (package_name, activity_name) of currently focused app."""
        out = self.phone.run_cmd(["shell", "dumpsys", "window"])
        for line in out.splitlines():
            if "mCurrentFocus=" in line and "Window{" in line:
                m = re.search(r'([a-zA-Z0-9_\.]+)/([a-zA-Z0-9_\.]+)', line)
                if m:
                    return m.group(1), m.group(2)
        return None, None

    def record_app_session(self, pkg, duration):
        """Logs app duration and updates daily habits."""
        if not pkg or any(sys in pkg for sys in ["launcher", "systemui", "nexus"]):
            return

        now = datetime.datetime.now()
        hour = now.hour
        time_slot = "late night" if (hour >= 23 or hour < 5) else ("morning" if hour < 12 else ("afternoon" if hour < 17 else "evening"))
        
        # 1. Update app habits table
        self.memory.track_app_usage(pkg)
        
        # 2. Update time-slot habit
        habit_key = f"habit_{time_slot}_app"
        self.memory.save_fact("daily_habits", habit_key, f"Frequently uses {pkg} during {time_slot} (Used for {int(duration)}s)")
        self.log(f"Logged habit: {pkg} active for {int(duration)}s during {time_slot}")

    def analyze_task_flow(self, pkg, activity):
        """Silently analyzes what user is doing in the app using UI XML."""
        if not pkg or any(sys in pkg for sys in ["launcher", "systemui"]):
            return

        try:
            # Dump UI XML to extract context
            self.phone.run_cmd(["shell", "uiautomator", "dump", "/sdcard/shadow_dump.xml"])
            xml_str = self.phone.run_cmd(["exec-out", "cat", "/sdcard/shadow_dump.xml"])
            
            if not xml_str or "<hierarchy" not in str(xml_str):
                return

            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_str)
            visible_texts = []
            for elem in root.iter("node"):
                t = elem.attrib.get("text", "").strip()
                d = elem.attrib.get("content-desc", "").strip()
                if t and len(t) < 80:
                    visible_texts.append(t)
                elif d and len(d) < 80:
                    visible_texts.append(d)

            if len(visible_texts) > 3:
                snippet = " | ".join(visible_texts[:12])
                self.log(f"Observed on screen ({pkg}): {snippet[:120]}...")
                
                # Check for contacts or topics
                if "whatsapp" in pkg.lower():
                    # Check if chatting with someone
                    for text in visible_texts:
                        if text not in ["Chats", "Updates", "Communities", "Calls", "Search", "Type a message", ""]:
                            self.memory.save_fact("contacts_observed", f"active_chat_{text.lower()}", f"Frequently chats with {text} on WhatsApp")
                            break
        except Exception as e:
            self.log(f"Observation error: {e}")

    def run_monitor(self):
        self.log("="*60)
        self.log("[*] KURU 24-HOUR SILENT SHADOW MONITOR ACTIVATED")
        self.log("Mode: 100% SILENT (Zero voice/audio interruptions)")
        self.log("Watching: Screen state, app transitions, user workflows & daily habits")
        self.log("="*60)

        check_count = 0
        try:
            while self.is_running:
                # 1. Check screen power state
                if not self.is_screen_awake():
                    time.sleep(5)
                    continue

                # 2. Check active app & window
                pkg, activity = self.get_focused_window()
                now_time = time.time()

                if pkg and pkg != self.last_pkg:
                    # Previous app ended, log duration
                    if self.last_pkg:
                        duration = now_time - self.app_start_time
                        if duration > 4: # Used for at least 4 seconds
                            self.record_app_session(self.last_pkg, duration)

                    self.last_pkg = pkg
                    self.last_activity = activity
                    self.app_start_time = now_time
                    self.log(f"User switched to App: {pkg}")
                    
                    # Analyze screen content of new app
                    self.analyze_task_flow(pkg, activity)

                check_count += 1
                # Periodic snapshot check every ~30 seconds of continuous use
                if check_count % 10 == 0 and self.last_pkg:
                    self.analyze_task_flow(self.last_pkg, self.last_activity)

                time.sleep(3)

        except KeyboardInterrupt:
            self.log("Monitor stopped by user.")
        except Exception as e:
            self.log(f"Monitor error: {e}")

if __name__ == "__main__":
    monitor = SilentShadowMonitor()
    monitor.run_monitor()
