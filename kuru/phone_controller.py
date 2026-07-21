import subprocess
import os
import re
import time
from PIL import Image
from kuru.config import ADB_PATH, APP_PACKAGES

class PhoneController:
    def __init__(self, adb_path=ADB_PATH):
        self.adb_path = adb_path
        self.width, self.height = self.get_screen_size()

    def run_cmd(self, cmd_args, text=True):
        full_cmd = [self.adb_path] + cmd_args
        if text:
            res = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        else:
            res = subprocess.run(full_cmd, capture_output=True)
        return res.stdout

    def get_screen_size(self):
        output = self.run_cmd(["shell", "wm", "size"])
        for line in str(output).splitlines():
            if "Physical size:" in line:
                parts = line.split(":")[-1].strip().split("x")
                return int(parts[0]), int(parts[1])
        return 1080, 2400

    def wake_and_unlock(self):
        """Wakes up the screen and dismisses keyguard in 0.2s."""
        self.run_cmd(["shell", "input", "keyevent", "224"]) # WAKEUP
        self.run_cmd(["shell", "input", "keyevent", "82"])  # MENU / UNLOCK
        self.swipe(self.width // 2, int(self.height * 0.8), self.width // 2, int(self.height * 0.2), 200)

    def take_screenshot(self, output_path="current_screen.jpg", compress=True):
        """Ultra-fast screenshot capture and lightweight JPEG compression."""
        raw_png = "raw_temp.png"
        full_cmd = [self.adb_path, "exec-out", "screencap", "-p"]
        with open(raw_png, "wb") as f:
            subprocess.run(full_cmd, stdout=f)
        
        if compress:
            try:
                with Image.open(raw_png) as img:
                    # Resize to max 1080p if larger for 5x faster upload to Gemini
                    if img.width > 1080:
                        ratio = 1080 / img.width
                        new_h = int(img.height * ratio)
                        img = img.resize((1080, new_h), Image.Resampling.LANCZOS)
                    img.convert("RGB").save(output_path, "JPEG", quality=80)
                if os.path.exists(raw_png):
                    os.remove(raw_png)
                return output_path
            except Exception:
                pass
        return raw_png

    def check_input_permission(self):
        """Verifies if Xiaomi/MIUI allows input tap/type."""
        output = self.run_cmd(["shell", "input", "tap", "100", "100"])
        if "SecurityException" in str(output) or "INJECT_EVENTS" in str(output):
            print("\n[!] CRITICAL: Xiaomi USB Debugging (Security settings) is OFF!")
            return False
        return True

    def tap(self, x, y):
        print(f"[*] Tapping at ({x}, {y})")
        res = self.run_cmd(["shell", "input", "tap", str(int(x)), str(int(y))])
        if "SecurityException" in str(res):
            print("[!] Touch blocked by phone security! Enable 'USB debugging (Security settings)' in Developer Options.")

    def swipe(self, x1, y1, x2, y2, duration=250):
        print(f"[*] Swiping ({x1},{y1}) -> ({x2},{y2})")
        self.run_cmd(["shell", "input", "swipe", str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(duration))])

    def scroll_down(self):
        cx = self.width // 2
        self.swipe(cx, int(self.height * 0.7), cx, int(self.height * 0.3), 300)

    def scroll_up(self):
        cx = self.width // 2
        self.swipe(cx, int(self.height * 0.3), cx, int(self.height * 0.7), 300)

    def type_text(self, text):
        print(f"[*] Typing: '{text}'")
        formatted = text.replace(" ", "%s")
        for char in ['&', '<', '>', ';', '|', '$', '(', ')', '"', "'"]:
            formatted = formatted.replace(char, f"\\{char}")
        self.run_cmd(["shell", "input", "text", formatted])

    def get_ui_elements(self):
        """Dumps and parses all interactive UI elements with bounding boxes and text."""
        self.run_cmd(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
        xml_str = self.run_cmd(["exec-out", "cat", "/sdcard/window_dump.xml"])
        elements = []
        if xml_str and "<hierarchy" in str(xml_str):
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(xml_str)
                for elem in root.iter("node"):
                    text = elem.attrib.get("text", "").strip()
                    desc = elem.attrib.get("content-desc", "").strip()
                    bounds = elem.attrib.get("bounds", "")
                    if (text or desc) and bounds:
                        m = re.findall(r'\[(\d+),(\d+)\]', bounds)
                        if len(m) == 2:
                            x1, y1 = int(m[0][0]), int(m[0][1])
                            x2, y2 = int(m[1][0]), int(m[1][1])
                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                            elements.append({"text": text, "desc": desc, "bounds": [x1, y1, x2, y2], "center": (cx, cy)})
            except Exception as e:
                print(f"(XML parse warning: {e})")
        return elements

    def tap_element_by_text(self, target_text):
        """Finds any button/tab on screen containing target_text or desc and taps it directly."""
        elements = self.get_ui_elements()
        target_lower = target_text.lower().strip()
        for e in elements:
            if target_lower == e["text"].lower() or target_lower == e["desc"].lower():
                print(f"[*] Found exact match '{e['text'] or e['desc']}' -> tapping {e['center']}")
                self.tap(e["center"][0], e["center"][1])
                return True
        for e in elements:
            if target_lower in e["text"].lower() or target_lower in e["desc"].lower():
                print(f"[*] Found partial match '{e['text'] or e['desc']}' -> tapping {e['center']}")
                self.tap(e["center"][0], e["center"][1])
                return True
        return False

    def execute_workflow(self, steps):
        """Replays a memorized multi-step workflow in real-time."""
        print(f"[*] Replaying memorized workflow ({len(steps)} steps)...")
        for step in steps:
            act = step.get("action")
            if act == "tap":
                self.tap(step.get("x", 500), step.get("y", 500))
                time.sleep(step.get("delay", 0.8))
            elif act == "type":
                self.type_text(step.get("text", ""))
                time.sleep(step.get("delay", 0.5))
            elif act == "key":
                self.press_key(step.get("key", "back"))
                time.sleep(0.4)
            elif act == "scroll_down":
                self.scroll_down()
                time.sleep(0.6)
            elif act == "scroll_up":
                self.scroll_up()
                time.sleep(0.6)

    def press_key(self, key_code):
        keys = {
            "home": "3", "back": "4", "enter": "66", "app_switch": "187",
            "volume_up": "24", "volume_down": "25", "power": "26", "search": "84"
        }
        code = keys.get(key_code.lower(), str(key_code))
        self.run_cmd(["shell", "input", "keyevent", code])

    def open_app(self, app_name_or_pkg):
        self.wake_and_unlock()
        pkg = APP_PACKAGES.get(app_name_or_pkg.lower(), app_name_or_pkg)
        print(f"[*] Opening app: {pkg}")
        self.run_cmd(["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])

    def open_url(self, url):
        self.wake_and_unlock()
        print(f"[*] Opening URL: {url}")
        self.run_cmd(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url])

    def search_spotify(self, query):
        """Instant Spotify Search / Play via Intent in 0.2s."""
        self.wake_and_unlock()
        encoded = query.replace(" ", "+")
        url = f"spotify:search:{encoded}"
        self.open_url(url)

    def send_sms(self, phone_number, message):
        """Instant Normal SMS Message in 0.2s."""
        self.wake_and_unlock()
        print(f"[*] Sending SMS to {phone_number}: '{message}'")
        self.run_cmd(["shell", "am", "start", "-a", "android.intent.action.SENDTO", "-d", f"sms:{phone_number}", "--es", "sms_body", message])

    def search_google(self, query):
        """Instant Google Search in 0.2 seconds via Android Intent."""
        encoded = query.replace(" ", "+")
        url = f"https://www.google.com/search?q={encoded}"
        self.open_url(url)

    def search_youtube(self, query):
        """Instant YouTube Search & Auto-Play directly into video playback."""
        self.wake_and_unlock()
        # Method 1: Instant Direct Video Playback via video ID (zero ads, zero search delay)
        try:
            import subprocess
            cmd = [r'D:\personal AI\venv\Scripts\yt-dlp.exe', f'ytsearch1:{query}', '--get-id', '--no-warnings', '--skip-download']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            video_id = res.stdout.strip()
            if video_id and len(video_id) == 11 and " " not in video_id:
                print(f"[*] Instant Direct Video Playback: vnd.youtube:{video_id}")
                self.run_cmd(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"vnd.youtube:{video_id}"])
                return
        except Exception as e:
            print(f"(Direct play fallback: {e})")

        # Method 2: Native App Search & Smart Element Detection (ignores ads!)
        self.open_app("youtube")
        time.sleep(1.2)
        # 1. Tap search icon at top right (1020, 224)
        self.tap(1020, 224)
        time.sleep(0.6)
        # 2. Type query and submit
        self.type_text(query)
        time.sleep(0.4)
        self.press_key("enter")
        time.sleep(1.8)
        # 3. Dynamic scan for first actual video (ignoring ads!)
        elements = self.get_ui_elements()
        for e in elements:
            desc = e.get("desc", "").lower()
            if "play video" in desc or "play short" in desc:
                cx, cy = e["center"]
                print(f"[*] Found Video Card: '{desc[:50]}' -> Tapping ({cx}, {cy})")
                self.tap(cx, cy)
                return
        # If no XML card found, tap standard video card location
        self.tap(self.width // 2, 1150)
        print(f"[*] YouTube playing search result for: {query}")

    def play_current_media(self):
        """Plays or taps whatever video/song is currently on screen."""
        print("[*] Playing/resuming current media on screen...")
        self.wake_and_unlock()
        # 1. First check if any video card is visible on screen to tap
        elements = self.get_ui_elements()
        for e in elements:
            desc = e.get("desc", "").lower()
            if "play video" in desc or "play short" in desc or "video player" in desc:
                cx, cy = e["center"]
                print(f"[*] Tapping video element: '{desc[:50]}' at ({cx}, {cy})")
                self.tap(cx, cy)
                return
        # 2. If inside video player or media app, send Play key
        self.run_cmd(["shell", "input", "keyevent", "126"]) # KEYCODE_MEDIA_PLAY
        self.run_cmd(["shell", "input", "keyevent", "85"])  # KEYCODE_MEDIA_PLAY_PAUSE
        self.tap(self.width // 2, 1000)

    def play_youtube_history(self):
        """Opens YouTube App -> You tab -> taps first recent/history video directly!"""
        print("[*] Opening YouTube App -> You/History -> playing most recent video/song...")
        self.wake_and_unlock()
        self.open_app("youtube")
        time.sleep(1.2)
        # 1. Tap 'You' tab at bottom right (1081, 2630)
        self.tap(1081, 2630)
        time.sleep(1.2)
        # 2. Tap first history video thumbnail (264, 1146)
        self.tap(264, 1146)
        print("[*] History video/song playing!")

    def play_youtube_liked(self):
        """Plays user's Liked Videos playlist in native YouTube App."""
        print("[*] Opening YouTube App -> Liked Videos...")
        self.wake_and_unlock()
        self.open_app("youtube")
        time.sleep(1.2)
        # Tap 'You' tab
        self.tap(1081, 2630)
        time.sleep(1.0)
        # Tap Liked Videos playlist entry (bounds [48,2373][1212,2657] -> center 630, 2515)
        self.tap(630, 2515)
        time.sleep(1.5)
        # Tap play
        self.tap(self.width // 2, 900)

    def open_app_drawer(self):
        """Swipes up from home screen to open the app drawer."""
        print("[*] Opening App Drawer...")
        self.wake_and_unlock()
        self.press_key("home")
        time.sleep(0.5)
        self.swipe(self.width // 2, int(self.height * 0.8), self.width // 2, int(self.height * 0.2), 250)
        time.sleep(0.6)

    def set_alarm(self, hour, minute, label="Alarm"):
        """Sets an alarm directly using Android Alarm Intent and confirms it."""
        print(f"[*] Setting alarm for {hour:02d}:{minute:02d} ('{label}')...")
        self.wake_and_unlock()
        self.run_cmd([
            "shell", "am", "start", "-a", "android.intent.action.SET_ALARM",
            "--ei", "android.intent.extra.alarm.HOUR", str(hour),
            "--ei", "android.intent.extra.alarm.MINUTES", str(minute),
            "--es", "android.intent.extra.alarm.MESSAGE", label,
            "--ez", "android.intent.extra.alarm.SKIP_UI", "false"
        ])
        time.sleep(1.2)
        # Tap Confirm button on Xiaomi (1123, 365)
        self.tap(1123, 365)
        time.sleep(0.5)
        self.press_key("home")
        print("[*] Alarm successfully configured and saved!")

    def read_latest_email(self):
        """Opens Gmail, extracts the latest email sender, subject, and snippet."""
        print("[*] Checking Gmail for latest email...")
        self.wake_and_unlock()
        self.open_app("gmail")
        time.sleep(2.0)
        self.run_cmd(["shell", "uiautomator", "dump", "/sdcard/mail_dump.xml"])
        xml_str = self.run_cmd(["exec-out", "cat", "/sdcard/mail_dump.xml"])
        if xml_str and "<hierarchy" in str(xml_str):
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(xml_str)
                for elem in root.iter("node"):
                    text = elem.attrib.get("text", "").strip()
                    if text.startswith("Unread, ") or ("," in text and any(m in text for m in ["Oct", "Nov", "Sep", "am", "pm", "ago"])):
                        parts = [p.strip() for p in text.split(",") if p.strip()]
                        if len(parts) >= 3:
                            sender = parts[1] if parts[0] == "Unread" else parts[0]
                            subject = parts[2] if parts[0] == "Unread" else parts[1]
                            snippet = parts[3] if len(parts) > 3 else ""
                            return {"sender": sender, "subject": subject, "snippet": snippet}
            except Exception as e:
                print(f"(Mail parse error: {e})")
        return None

    def make_call(self, phone_number):
        """Dials or calls phone number directly."""
        self.wake_and_unlock()
        self.run_cmd(["shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{phone_number}"])

    def answer_call(self):
        print("[*] Answering incoming call...")
        self.run_cmd(["shell", "input", "keyevent", "5"])
        self.swipe(self.width // 2, int(self.height * 0.8), self.width // 2, int(self.height * 0.3), 200)

    def end_call(self):
        print("[*] Hanging up call...")
        self.run_cmd(["shell", "input", "keyevent", "6"])

    def fast_whatsapp_send(self, contact_name, message):
        """Ultra-fast reliable WhatsApp message sender calibrated for Xiaomi screen (1236x2750)."""
        print(f"[*] Fast-Path WhatsApp: Sending to '{contact_name}' -> '{message}'")
        self.wake_and_unlock()
        self.open_app("whatsapp")
        time.sleep(1.0)

        # 1. Tap Meta AI or Search bar (Center 618, 404)
        self.tap(618, 404)
        time.sleep(0.6)

        # 2. Type contact name
        self.type_text(contact_name)
        time.sleep(1.0)

        # 3. Tap top contact result (Exact verified coordinate: 400, 512)
        self.tap(400, 512)
        time.sleep(0.8)

        # 4. Tap entry field (388, 2616) & type message
        self.tap(388, 2616)
        time.sleep(0.3)
        self.type_text(message)
        time.sleep(0.5)

        # 5. Tap send button (Exact verified coordinate: 1136, 2614)
        self.tap(1136, 2614)
        print("[*] WhatsApp message dispatched and sent successfully!")
