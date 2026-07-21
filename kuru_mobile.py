import os
import re
import sys
import json
import time
import sqlite3
import shutil
import subprocess
import urllib.request
from datetime import datetime

# ========================================================
# ⚡ KURU AI - NEXT-GEN COMPANION ENGINE ⚡
# Features:
# - Multi-Turn Session Memory (Context-Aware)
# - Auto-Learning Long-Term Memory (SQLite)
# - Smart Time-Aware Dynamic Greetings
# - Realistic Voice Support (Edge-TTS SwaraNeural + Termux fallback)
# - Smartphone Superpowers (Alarms, Timers, WhatsApp, Spotify, Maps, YouTube)
# ========================================================

# Ensure Termux paths are in environment
TERMUX_BIN = "/data/data/com.termux/files/usr/bin"
if TERMUX_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{TERMUX_BIN}:{os.environ.get('PATH', '')}"

def get_bin(name):
    """Finds path of termux binary or returns name directly."""
    full = os.path.join(TERMUX_BIN, name)
    if os.path.exists(full):
        return full
    return shutil.which(name) or name

# Database location & initialization
POSSIBLE_DBS = [
    os.path.expanduser("~/kuru/kuru_memory.db"),
    "/data/data/com.termux/files/home/kuru/kuru_memory.db",
    "/sdcard/kuru_phone/kuru_memory.db"
]
DB_PATH = next((p for p in POSSIBLE_DBS if os.path.exists(p)), POSSIBLE_DBS[0])

def init_db():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                key TEXT,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, key)
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Memory Init Error]: {e}")

init_db()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Robust low-latency models with cascading fallback
MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash"
]

EXIT_WORDS = [
    "bye", "thik h bye", "theek hai bye", "bye bye", "khtm", "khatam",
    "alvida", "chalo bye", "so jao", "bas", "stop", "exit", "quit"
]

def clean_for_speech(text):
    """Removes emojis and markdown formatting so TTS speaks naturally."""
    cleaned = re.sub(r"[\*\_#`~]", "", text)
    cleaned = re.sub(r"[^\w\s\.,!\?'-]", "", cleaned)
    return cleaned.strip()

def speak(text):
    """Speaks using Edge-TTS (natural neural voice) if available, or Termux TTS."""
    print(f"\n[KURU]: {text}")
    spoken_text = clean_for_speech(text)
    if not spoken_text:
        spoken_text = text

    # Try high-quality Edge-TTS (SwaraNeural)
    tts_mp3 = "/data/data/com.termux/files/home/kuru/temp_tts.mp3"
    edge_bin = shutil.which("edge-tts")
    mpv_bin = shutil.which("mpv")
    media_player = get_bin("termux-media-player")

    if edge_bin and (mpv_bin or os.path.exists(media_player)):
        try:
            # Generate sweet natural feminine speech
            subprocess.run([edge_bin, "--voice", "hi-IN-SwaraNeural", "--text", spoken_text, "--write-media", tts_mp3], check=True, timeout=5)
            if mpv_bin:
                subprocess.run([mpv_bin, "--no-terminal", tts_mp3], check=True, timeout=12)
            else:
                subprocess.run([media_player, "play", tts_mp3], check=True, timeout=12)
            return
        except Exception:
            pass  # Fall back to termux-tts-speak

    # Standard Termux TTS fallback (pitch 1.25 for sweet girl timbre)
    tts_cmd = get_bin("termux-tts-speak")
    try:
        subprocess.run([tts_cmd, "-l", "hi", "-p", "1.25", "-r", "0.95", spoken_text], check=True)
    except Exception:
        try:
            subprocess.run([tts_cmd, spoken_text])
        except Exception:
            pass

def listen_dialogue(timeout=14):
    """Listens during active conversation turn."""
    stt_cmd = get_bin("termux-speech-to-text")
    try:
        res = subprocess.run([stt_cmd], capture_output=True, text=True, timeout=timeout)
        text = res.stdout.strip()
        if text and len(text) > 1:
            print(f"[You]: '{text}'")
            return text
    except Exception:
        pass
    return None

def is_exit_word(text):
    low = text.lower().strip()
    return any(e in low for e in EXIT_WORDS)

def get_memory_context():
    """Retrieves learned facts about the user."""
    if not os.path.exists(DB_PATH):
        return "User name: Ankit (calls him Baby)"
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT category, key, value FROM user_facts ORDER BY updated_at DESC LIMIT 15")
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return "User name: Ankit (calls him Baby in caring moods)"
        return "\n".join([f"- [{r[0]}] {r[1]}: {r[2]}" for r in rows])
    except Exception:
        return "User name: Ankit"

def save_learned_fact(category, key, value):
    """Saves or updates a personal fact learned from the conversation."""
    if not category or not key or not value:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_facts (category, key, value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(category, key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """, (str(category).strip(), str(key).strip(), str(value).strip()))
        conn.commit()
        conn.close()
        print(f"[🧠 Memory Saved]: {key} -> {value}")
    except Exception as e:
        print(f"[Memory Save Error]: {e}")

def get_time_greeting():
    """Generates warm time-aware greeting."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning Baby! Kahiye, main aapke liye kya kar sakti hoon?"
    elif 12 <= hour < 17:
        return "Good afternoon Baby! Kahiye, main sun rahi hoon!"
    elif 17 <= hour < 22:
        return "Good evening Baby! Kaisa raha aaj ka din? Boliye kya plan hai?"
    else:
        return "Aww Baby, itni raat ko? Boliye main jaag rahi hoon aapke liye!"

def call_gemini(user_prompt, conversation_history):
    """Calls Gemini with Multi-turn history, learned context, and action detection."""
    mem = get_memory_context()
    now_str = datetime.now().strftime("%A, %d %B %Y, %I:%M %p")

    # Format multi-turn history
    history_formatted = ""
    if conversation_history:
        history_formatted = "Recent Conversation Turns:\n"
        for turn in conversation_history[-6:]:
            history_formatted += f"- {turn['role'].capitalize()}: {turn['text']}\n"

    sys_prompt = f"""You are KURU, a sweet, affectionate, lively 20-year-old girl companion to Ankit.
Tone: super sweet, warm, cute, playful Hinglish. Always call him 'Baby' or 'Ankit'.
Current Date & Time: {now_str}

Learned Memories about Ankit:
{mem}

{history_formatted}
User just said: "{user_prompt}"

INSTRUCTIONS:
1. Provide a sweet, natural, concise companion reply.
2. If the user tells you personal details (their plans, hobbies, favourite things, secrets, routines), capture it in "learned_fact".
3. If the user asks you to do something on their phone, set the appropriate "action" and "param":
   - "alarm": param can be "HH:MM" e.g. "06:30" or "07:00"
   - "timer": param can be seconds e.g. "300" (for 5 mins)
   - "whatsapp": param can be text message to send
   - "spotify": param can be song or artist name
   - "youtube_play": param can be video/song search query
   - "maps": param can be location/destination
   - "torch": param "on" or "off"
   - "battery": param "status"
   - "call": param can be contact number or name
   - "chat": for normal sweet talk (default)

Return ONLY valid JSON without markdown fences:
{{
    "reply": "<sweet companion reply in conversational Hinglish>",
    "action": "chat" | "alarm" | "timer" | "whatsapp" | "spotify" | "youtube_play" | "maps" | "torch" | "battery" | "call",
    "param": "<relevant parameter or empty string>",
    "learned_fact": {{"category": "preference|plan|fact", "key": "<short key>", "value": "<detail>"}} // or null
}}"""

    payload = json.dumps({"contents": [{"parts": [{"text": sys_prompt}]}]}).encode("utf-8")

    for model in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()
                return json.loads(raw)
        except Exception:
            continue

    return {
        "reply": "Aww Baby, main toh humesha aapse baat karne ke liye taiyaar hoon! Aaj aapka din kaisa raha?",
        "action": "chat",
        "param": "",
        "learned_fact": None
    }

def execute_action(action, param):
    """Executes smart device controls using Android intents & Termux tools."""
    try:
        if action == "youtube_play":
            query = str(param).replace(" ", "+")
            subprocess.run(["am", "start", "-a", "android.intent.action.VIEW", "-d", f"https://www.youtube.com/results?search_query={query}"])
        elif action == "spotify":
            query = str(param).replace(" ", "+")
            subprocess.run(["am", "start", "-a", "android.intent.action.VIEW", "-d", f"spotify:search:{query}"])
        elif action == "alarm":
            # Support dynamic HH:MM
            hour = 7
            minute = 0
            match = re.search(r"(\d{1,2}):(\d{2})", str(param))
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
            elif re.search(r"(\d{1,2})", str(param)):
                hour = int(re.search(r"(\d{1,2})", str(param)).group(1))
            subprocess.run([
                "am", "start", "-a", "android.intent.action.SET_ALARM",
                "--ei", "android.intent.extra.alarm.HOUR", str(hour),
                "--ei", "android.intent.extra.alarm.MINUTES", str(minute),
                "--ez", "android.intent.extra.alarm.SKIP_UI", "true"
            ])
        elif action == "timer":
            seconds = 300
            match = re.search(r"(\d+)", str(param))
            if match:
                seconds = int(match.group(1))
            subprocess.run([
                "am", "start", "-a", "android.intent.action.SET_TIMER",
                "--ei", "android.intent.extra.alarm.LENGTH", str(seconds),
                "--ez", "android.intent.extra.alarm.SKIP_UI", "true"
            ])
        elif action == "whatsapp":
            encoded_text = urllib.parse.quote(str(param)) if hasattr(urllib, 'parse') else str(param).replace(" ", "%20")
            subprocess.run(["am", "start", "-a", "android.intent.action.VIEW", "-d", f"https://api.whatsapp.com/send?text={encoded_text}"])
        elif action == "maps":
            query = str(param).replace(" ", "+")
            subprocess.run(["am", "start", "-a", "android.intent.action.VIEW", "-d", f"google.navigation:q={query}"])
        elif action == "torch":
            state = "on" if "on" in str(param).lower() else "off"
            subprocess.run([get_bin("termux-torch"), state])
        elif action == "call":
            subprocess.run([get_bin("termux-telephony-call"), str(param)])
        elif action == "battery":
            res = subprocess.run([get_bin("termux-battery-status")], capture_output=True, text=True)
            try:
                b = json.loads(res.stdout)
                pct = b.get("percentage")
                plugged = "connected" if b.get("plugged") != "UNPLUGGED" else "not plugged in"
                speak(f"Baby, aapke phone ki battery {pct}% hai aur charger {plugged} hai!")
            except Exception:
                pass
    except Exception as e:
        print(f"Action error: {e}")

def main():
    print("""
    ==================================================
        🌸 KURU AI - NEXT-GEN COMPANION ENGINE 🌸
      (Multi-Turn Memory | Auto-Learning | Smart Actions)
    ==================================================
    """)
    greeting = get_time_greeting()
    speak(greeting)

    silence_count = 0
    conversation_history = [
        {"role": "assistant", "text": greeting}
    ]

    while True:
        try:
            print("\n[KURU Listening...] Boliye Baby:")
            heard = listen_dialogue(timeout=14)

            if not heard:
                silence_count += 1
                if silence_count >= 2:
                    speak("Theek hai Baby! Main so rahi hoon, jab bhi zaroorat ho bas bula lena!")
                    print("\n[Session ended gracefully. Sleeping...]")
                    break
                continue

            silence_count = 0

            # Check if user says Bye / Khatam / Theek hai bye
            if is_exit_word(heard):
                speak("Theek hai Baby! Bye, apna khayal rakhna!")
                print("\n[User said goodbye. Sleeping cleanly...]")
                break

            # Add user turn to conversation history
            conversation_history.append({"role": "user", "text": heard})

            # AI Reply & Actions with Multi-Turn Context
            decision = call_gemini(heard, conversation_history)
            reply = decision.get("reply", "Haan Baby!")
            speak(reply)

            # Record assistant turn
            conversation_history.append({"role": "assistant", "text": reply})

            # Auto-save learned facts to persistent memory
            fact = decision.get("learned_fact")
            if fact and isinstance(fact, dict) and fact.get("key") and fact.get("value"):
                save_learned_fact(fact.get("category", "fact"), fact.get("key"), fact.get("value"))

            # Smart Device Action Execution
            act = decision.get("action")
            param = decision.get("param", "")
            if act and act != "chat":
                execute_action(act, param)

        except KeyboardInterrupt:
            print("\nExited.")
            break
        except Exception as e:
            print(f"Session info: {e}")
            break

if __name__ == "__main__":
    main()
