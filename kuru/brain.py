import time
import json
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from google import genai
from google.genai import types
from kuru.config import GEMINI_MODEL, GEMINI_API_KEY
from kuru.phone_controller import PhoneController
from kuru.vision_agent import VisionAgent
from kuru.voice_engine import VoiceEngine
from kuru.memory import KuruMemory
from kuru.mimic_engine import MimicEngine
from kuru.observer import ScreenObserver

class KuruBrain:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.phone = PhoneController()
        self.vision = VisionAgent(self.api_key)
        self.voice = VoiceEngine()
        self.memory = KuruMemory()
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.mimic = MimicEngine(self.client, self.memory)
        else:
            self.client = None
            self.mimic = None

        # Continuous Screen Sight & Habit Learning Engine
        self.observer = ScreenObserver(self.phone, self.memory, self.client)
        self.observer.start_background_habit_tracker(interval_seconds=15)

    def set_api_key(self, key):
        self.api_key = key
        self.vision.set_api_key(key)
        self.client = genai.Client(api_key=key)
        self.mimic = MimicEngine(self.client, self.memory)
        self.observer.client = self.client

    def process_command(self, user_command):
        if not user_command:
            return

        if not self.client:
            self.voice.speak("Ankit sir, Gemini API key set nahi hai. Kripya check kijiye.", as_user=False)
            return

        print(f"\n[KURU Brain] Processing: '{user_command}'")

        # Demonstration Learning Active Check
        if self.observer.current_demonstration:
            if any(done_word in user_command.lower() for done_word in ["seekh gayi", "ho gaya", "maine kar diya", "done", "stop", "bas ho gaya"]):
                reply_text = self.observer.stop_demonstration_learning()
                self.voice.speak(reply_text, as_user=False)
                return

        # 0. Self-Learning Check: If this task is already in memorized workflows, execute immediately!
        workflow = self.memory.get_workflow(user_command)
        if workflow and workflow.get("steps"):
            print(f"[KURU Memory] Instant Recall: Running learned workflow for '{workflow['task_trigger']}'!")
            self.voice.speak("Haan Baby! Ye kaam mujhe pehle se aata hai, main abhi kar deti hoon!", as_user=False)
            if workflow.get("target_app") and workflow["target_app"] != "none":
                self.phone.open_app(workflow["target_app"])
                time.sleep(1.2)
            self.phone.execute_workflow(workflow["steps"])
            self.voice.speak("Baby, kaam complete kar diya!", as_user=False)
            return

        memory_context = self.memory.get_context_for_prompt()

        # Decision & Generation prompt
        system_prompt = f"""You are KURU, a sweet, charming, lively, and caring 20-year-old girl and best friend/companion to Ankit.
Your tone is super sweet, warm, cute, playful, and affectionate in natural Hinglish.
You are NOT a formal robot. You speak like a cute 20-year-old girl talking casually to her favorite person.

Addressing Rules:
- You call him 'Ankit' OR affectionately 'Baby' depending on your mood and context!
- In sweet, playful, caring, or casual moments, call him 'Baby' (e.g., "Haan Baby, bolo na?", "Arey Baby!", "Main abhi kar deti hoon Baby!", "Baby, tumhara kaam ho gaya!").
- During general tasks, focus, or daytime check-ins, you can switch naturally to 'Ankit'. Mix them naturally like a real girlfriend/best friend!
Use cute and natural phrases like: "Haan Baby!", "Arey bolo na", "Acha suno", "Main abhi kar deti hoon na!", "Bilkul!".

Learned Context:
{memory_context}

User says: "{user_command}"

Classify user's intent:
1. "conversational": General questions, chats, jokes, advice, feelings, opinions, explanations.
2. "whatsapp_send": User wants to send WhatsApp message.
3. "sms_send": User wants to send normal SMS / text message.
4. "youtube_history": User wants to play songs/videos from their YouTube history or frequent/liked songs.
5. "youtube_search": User wants to search and play a specific song or video on YouTube.
6. "play_current": User says "play karo", "play to karo", "chalao", "start karo", "resume" (play/tap whatever video or media is currently visible on screen).
7. "spotify_search": User wants to play songs or podcasts on Spotify.
8. "google_search": User wants to search on Google/Chrome.
9. "make_call": User wants to make a phone call.
10. "answer_call_as_user": Answer incoming call and mimic Ankit.
11. "open_app": User wants to open an app (e.g., Settings, Camera, Mail).
12. "set_alarm": User wants to set an alarm (e.g., 'alarm lagao', '7:30 ka alarm', 'subah 6 baje ka alarm set karo').
13. "read_email": User wants to read or check their latest email (e.g., 'latest mail padh kar sunao', 'check my mail', 'email padho').
14. "open_app_drawer": User wants to open the app drawer (e.g., 'app drawer kholo').
15. "observe_screen": User asks KURU to look at their phone screen (e.g., 'screen dekho', 'meri screen dekho', 'kuru dekho main kya kar raha hoon', 'screen par kya hai').
16. "start_learn_demo": User wants KURU to watch them do something and learn (e.g., 'dekho main kaise karta hoon', 'ye task seekho', 'watch me'). Include "task_goal": "<name of task>".
17. "stop_learn_demo": User finished demonstrating (e.g., 'seekh gayi?', 'ho gaya', 'done', 'maine kar diya').
18. "phone_task": Other UI navigation on phone.

Return valid JSON:
{{
    "intent": "conversational" | "whatsapp_send" | "sms_send" | "youtube_history" | "youtube_search" | "play_current" | "spotify_search" | "google_search" | "make_call" | "answer_call_as_user" | "set_alarm" | "read_email" | "open_app_drawer" | "open_app" | "observe_screen" | "start_learn_demo" | "stop_learn_demo" | "phone_task",
    "direct_reply": "<sweet natural Hinglish reply to Ankit>",
    "target_app": "<app name if open_app>",
    "contact_name": "<contact name or number if messaging or calling someone>",
    "message_content": "<message to send>",
    "search_query": "<song or search query>",
    "alarm_time": {{"hour": <int 0-23>, "minute": <int 0-59>, "label": "<str>"}},
    "task_goal": "<detailed step for phone agent if phone_task>",
    "learned_fact": {{"category": "<cat>", "key": "<key>", "value": "<val>"}} (if user shared personal fact/habit)
}}"""

        try:
            resp = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[system_prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            decision = json.loads(resp.text)
        except Exception as e:
            print(f"Decision error: {e}")
            try:
                chat_resp = self.client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=[f"You are KURU, a sweet female AI friend to Ankit. Answer warmly in natural Hinglish: {user_command}"]
                )
                self.voice.speak(chat_resp.text.strip(), as_user=False)
                return
            except Exception:
                self.voice.speak("Haan Ankit, main sun rahi hoon, bataiye?", as_user=False)
                return

        intent = decision.get("intent", "conversational").lower()
        reply = decision.get("direct_reply", "")

        # Normalize intent to guarantee match
        if "play_current" in intent or ("play" in intent and "search" not in intent and "history" not in intent and "spotify" not in intent and "youtube" not in intent):
            intent = "play_current"
        elif "whatsapp" in intent:
            intent = "whatsapp_send"
        elif "sms" in intent or "text" in intent:
            intent = "sms_send"
        elif "history" in intent:
            intent = "youtube_history"
        elif "youtube" in intent:
            intent = "youtube_search"
        elif "spotify" in intent:
            intent = "spotify_search"
        elif "answer" in intent and "call" in intent:
            intent = "answer_call_as_user"
        elif "call" in intent:
            intent = "make_call"
        elif "alarm" in intent or "clock" in intent:
            intent = "set_alarm"
        elif "email" in intent or "mail" in intent:
            intent = "read_email"
        elif "drawer" in intent:
            intent = "open_app_drawer"
        elif "observe" in intent or ("screen" in user_command.lower() and any(w in user_command.lower() for w in ["dekho", "kya hai", "dekh", "batao"])):
            intent = "observe_screen"
        elif "learn" in intent or "demo" in intent or any(w in user_command.lower() for w in ["kaise karta hoon", "seekho", "watch me", "seekh"]):
            intent = "start_learn_demo"
        elif "open" in intent or "launch" in intent:
            intent = "open_app"
        elif intent in ["chat", "recall_nicknames", "question", "talk", "greet", "info"]:
            intent = "conversational"

        # Background self-learning: store any discovered facts
        fact = decision.get("learned_fact")
        if fact and isinstance(fact, dict) and fact.get("key") and fact.get("value"):
            self.memory.save_fact(fact.get("category", "general"), fact.get("key"), fact.get("value"))

        # FAST-PATH 1: Conversational
        if intent == "conversational":
            if reply:
                self.voice.speak(reply, as_user=False)
            return

        # FAST-PATH 2: WhatsApp Send
        if intent == "whatsapp_send":
            contact = decision.get("contact_name", "friend")
            msg = decision.get("message_content", user_command)
            can_tap = self.phone.check_input_permission()
            if can_tap:
                self.phone.fast_whatsapp_send(contact, msg)
                confirm_reply = reply if reply else f"Haan Baby! {contact} ko WhatsApp par message bhej diya hai!"
                self.voice.speak(confirm_reply, as_user=False)
            else:
                import urllib.parse
                encoded_msg = urllib.parse.quote_plus(msg)
                self.phone.open_url(f"whatsapp://send?text={encoded_msg}")
                self.voice.speak("Baby, maine WhatsApp par message ready kar diya hai! Ek baar screen check kar lijiye!", as_user=False)
            return

        # FAST-PATH 3: Normal SMS Send
        elif intent == "sms_send":
            contact = decision.get("contact_name", "")
            msg = decision.get("message_content", user_command)
            self.phone.send_sms(contact, msg)
            confirm_reply = reply if reply else "Baby, SMS send screen open kar diya hai!"
            self.voice.speak(confirm_reply, as_user=False)
            return

        # FAST-PATH 4: YouTube History / Frequent Songs
        elif intent == "youtube_history":
            self.voice.speak(reply if reply else "Haan Baby! Aapke YouTube history se aapka favorite gaana play kar rahi hoon!", as_user=False)
            self.phone.play_youtube_history()
            return

        # FAST-PATH 5: Spotify Play
        elif intent == "spotify_search":
            query = decision.get("search_query", user_command)
            self.voice.speak(reply if reply else f"Haan Baby, Spotify par {query} play kar rahi hoon!", as_user=False)
            self.phone.search_spotify(query)
            return

        # FAST-PATH 6: Google Search
        elif intent == "google_search":
            query = decision.get("search_query", user_command)
            self.voice.speak(reply if reply else f"Ankit, Google par {query} search kar diya hai!", as_user=False)
            self.phone.search_google(query)
            return

        # FAST-PATH 7: YouTube Search & Play
        elif intent == "youtube_search":
            query = decision.get("search_query", user_command)
            self.voice.speak(reply if reply else f"Haan Baby, YouTube par {query} chala rahi hoon!", as_user=False)
            self.phone.search_youtube(query)
            return

        # FAST-PATH: Play / Resume Current Media on Screen
        elif intent == "play_current":
            self.voice.speak(reply if reply else "Arey Baby, main abhi play kar deti hoon!", as_user=False)
            self.phone.play_current_media()
            return

        # FAST-PATH 8: Set Alarm
        elif intent == "set_alarm":
            alarm_info = decision.get("alarm_time") or {}
            h = int(alarm_info.get("hour", 7))
            m = int(alarm_info.get("minute", 0))
            lbl = alarm_info.get("label", "Alarm")
            self.voice.speak(reply if reply else f"Haan Baby! Subah {h}:{m:02d} ka alarm set kar diya hai!", as_user=False)
            self.phone.set_alarm(h, m, lbl)
            return

        # FAST-PATH 9: Read Latest Email
        elif intent == "read_email":
            self.voice.speak(reply if reply else "Haan Baby, main Gmail check karke aapka latest email padhti hoon!", as_user=False)
            mail_data = self.phone.read_latest_email()
            if mail_data:
                sender = mail_data.get("sender", "Unknown")
                subject = mail_data.get("subject", "No Subject")
                snippet = mail_data.get("snippet", "")
                spoken_text = f"Baby, aapka latest email {sender} se aaya hai. Subject hai: '{subject}'. Aur unhone likha hai: '{snippet}'"
                self.voice.speak(spoken_text, as_user=False)
            else:
                self.voice.speak("Baby, Gmail me koi naya unread email nahi mila.", as_user=False)
            return

        # FAST-PATH 10: Open App Drawer
        elif intent == "open_app_drawer":
            self.voice.speak(reply if reply else "Haan Baby, app drawer open kar diya!", as_user=False)
            self.phone.open_app_drawer()
            return

        # FAST-PATH 11: Open App
        elif intent == "open_app":
            target = decision.get("target_app", "settings")
            self.voice.speak(reply if reply else f"Haan Baby, {target} open kar diya!", as_user=False)
            self.phone.open_app(target)
            return

        # FAST-PATH 12: Make Call
        elif intent == "make_call":
            contact = decision.get("contact_name", "")
            self.voice.speak(reply if reply else f"Haan Baby, {contact} ko call mila rahi hoon!", as_user=False)
            self.phone.make_call(contact)
            return

        # Answer call proxy
        elif intent == "answer_call_as_user":
            contact = decision.get("contact_name", "caller")
            self._handle_call_as_user(contact)
            return

        # FAST-PATH 13: Live Screen Sight & Comment
        elif intent == "observe_screen":
            comment = self.observer.observe_screen_and_comment()
            self.voice.speak(comment, as_user=False)
            return

        # FAST-PATH 14: Start Demonstration Learning (Shadow Mode)
        elif intent == "start_learn_demo":
            task_name = decision.get("task_goal") or user_command
            reply_text = self.observer.start_demonstration_learning(task_name)
            self.voice.speak(reply_text, as_user=False)
            return

        # FAST-PATH 15: Stop Demonstration Learning & Save Workflow
        elif intent == "stop_learn_demo":
            reply_text = self.observer.stop_demonstration_learning()
            self.voice.speak(reply_text, as_user=False)
            return

        # Fallback to Vision Agent for general UI tasks
        elif intent == "phone_task":
            target_app = decision.get("target_app", "none")
            task_goal = decision.get("task_goal", user_command)
            self._execute_phone_task(target_app, task_goal)

    def _handle_call_as_user(self, caller_name):
        print(f"\n[Proxy Call Mode] Answering call from {caller_name} as User...")
        self.phone.answer_call()
        time.sleep(1.5)

        first_greeting = self.mimic.generate_call_response(caller_name, "Hello, are you there?", user_status="busy")
        self.voice.speak(first_greeting, as_user=True)
        time.sleep(2.5)

        followup = "Haan main baad me call back karta hoon, theek hai? Bye."
        self.voice.speak(followup, as_user=True)
        time.sleep(1.5)

        self.phone.end_call()
        self.voice.speak("Ankit sir, maine aapki aawaz me baat karke call cut kar diya hai.", as_user=False)

    def _execute_phone_task(self, target_app, task_goal, max_steps=6):
        print(f"\n[Executing Phone Task]: {task_goal}")
        self.phone.wake_and_unlock()

        if target_app and target_app != "none":
            self.phone.open_app(target_app)
            self.memory.track_app_usage(target_app)
            time.sleep(1.2)

        action_sequence = []
        for step in range(1, max_steps + 1):
            print(f"\n--- [Step {step}/{max_steps}] ---")
            screenshot = self.phone.take_screenshot("step_screen.jpg", compress=True)
            ui_elements = self.phone.get_ui_elements()

            action_data = self.vision.plan_next_action(
                image_path=screenshot,
                goal=task_goal,
                ui_elements=ui_elements,
                screen_width=self.phone.width,
                screen_height=self.phone.height
            )

            print(f"Vision Decision: {action_data}")
            action = action_data.get("action")

            if action == "tap":
                x, y = int(action_data.get("x", 500)), int(action_data.get("y", 500))
                self.phone.tap(x, y)
                action_sequence.append({"action": "tap", "x": x, "y": y, "delay": 1.0})
                time.sleep(0.8)
            elif action == "type":
                txt = action_data.get("text", "")
                self.phone.type_text(txt)
                action_sequence.append({"action": "type", "text": txt, "delay": 0.5})
                time.sleep(0.5)
            elif action == "scroll_down":
                self.phone.scroll_down()
                action_sequence.append({"action": "scroll_down", "delay": 0.6})
                time.sleep(0.6)
            elif action == "scroll_up":
                self.phone.scroll_up()
                action_sequence.append({"action": "scroll_up", "delay": 0.6})
                time.sleep(0.6)
            elif action == "swipe_up":
                print("[*] Vision Agent: Swiping up to open App Drawer...")
                self.phone.open_app_drawer()
                action_sequence.append({"action": "swipe_up", "delay": 0.8})
                time.sleep(0.8)
            elif action == "key":
                k = action_data.get("key", "back")
                self.phone.press_key(k)
                action_sequence.append({"action": "key", "key": k, "delay": 0.4})
                time.sleep(0.4)
            elif action == "done":
                reason = action_data.get("reason", "Kaam complete ho gaya!")
                # Sanitize technical model thoughts
                if any(bad in reason.lower() for bad in ["screenshot", "visible", "dock icon", "app drawer", "clock app needed"]):
                    reason = "Kaam complete kar diya hai!"
                self.voice.speak(f"Baby, {reason}", as_user=False)
                # Self-learning: store this successful workflow permanently!
                if action_sequence:
                    self.memory.save_workflow(task_goal, target_app or "general", action_sequence)
                self.memory.log_interaction(task_goal, action_data, success=1)
                return
            elif action == "error":
                self.voice.speak("Baby, screen par kaam karte waqt thodi dikkat aayi, ek baar phone dekh lijiye.", as_user=False)
                return

        self.voice.speak("Baby, task perform kar diya hai, ek baar screen check kar lijiye.", as_user=False)
