import os
import re
import json
import base64
import asyncio
import datetime
import urllib.request
import streamlit as st

# ========================================================
# 🌸 KURU AI — LIVE WEB VOICE COMPANION 🌸
# Direct Voice & Audio Support (Listen + Speak in Browser)
# ========================================================

st.set_page_config(
    page_title="KURU AI — Your Sweet Voice Companion",
    page_icon="🌸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for gorgeous, modern aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at top, #2b1022 0%, #110714 60%, #08030b 100%);
        color: #fce7f3;
    }
    
    .header-box {
        text-align: center;
        padding: 22px 12px;
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.15), rgba(168, 85, 247, 0.12));
        border: 1px solid rgba(244, 114, 182, 0.25);
        border-radius: 20px;
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(236, 72, 153, 0.15);
    }
    
    .avatar-glow {
        width: 85px;
        height: 85px;
        margin: 0 auto 10px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ec4899, #8b5cf6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 38px;
        box-shadow: 0 0 25px rgba(236, 72, 153, 0.6);
        animation: pulse 3s infinite alternate;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 18px rgba(236, 72, 153, 0.5); }
        100% { transform: scale(1.05); box-shadow: 0 0 32px rgba(236, 72, 153, 0.85); }
    }
    
    .title-text {
        font-size: 24px;
        font-weight: 700;
        background: linear-gradient(to right, #f472b6, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    
    .subtitle-text {
        color: #fbcfe8;
        font-size: 13.5px;
        opacity: 0.9;
    }
    
    .voice-badge {
        display: inline-block;
        padding: 4px 12px;
        background: rgba(236, 72, 153, 0.2);
        border: 1px solid rgba(244, 114, 182, 0.35);
        border-radius: 14px;
        font-size: 12px;
        font-weight: 600;
        color: #f472b6;
        margin-top: 6px;
    }
    
    .stChatMessage {
        border-radius: 16px;
        padding: 12px 16px;
        margin-bottom: 12px;
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(244, 114, 182, 0.15);
    }
    
    /* Microphone Section Styling */
    div[data-testid="stAudioInput"] {
        border-radius: 18px !important;
        background: rgba(236, 72, 153, 0.08) !important;
        border: 1.5px dashed rgba(244, 114, 182, 0.4) !important;
        padding: 8px 12px !important;
        margin-bottom: 16px !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Configuration & Models -----------------
MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash"
]

def get_api_key():
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    if os.getenv("GEMINI_API_KEY"):
        return os.getenv("GEMINI_API_KEY")
    return st.session_state.get("user_gemini_key", "")

# ----------------- Time-Aware Greeting -----------------
def get_time_greeting():
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning Baby! Kahiye, main aapke liye kya kar sakti hoon?"
    elif 12 <= hour < 17:
        return "Good afternoon Baby! Kahiye, main sun rahi hoon!"
    elif 17 <= hour < 22:
        return "Good evening Baby! Kaisa raha aaj ka din? Boliye kya plan hai?"
    else:
        return "Aww Baby, itni raat ko? Boliye main jaag rahi hoon aapke liye!"

# ----------------- Text-to-Speech (Edge-TTS) -----------------
async def generate_speech_edge(text):
    import edge_tts
    clean = re.sub(r"[\*\_#`~]", "", text)
    clean = re.sub(r"[^\w\s\.,!\?'-]", "", clean).strip()
    if not clean:
        clean = text
    
    communicate = edge_tts.Communicate(clean, voice="hi-IN-SwaraNeural")
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes

def text_to_speech(text):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(generate_speech_edge(text))
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

# ----------------- Gemini Multimodal Audio Call -----------------
def call_kuru_audio(audio_bytes, mime_type, chat_history, api_key):
    """Processes user voice recording directly with Gemini multimodal audio."""
    now_str = datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    
    history_str = ""
    for msg in chat_history[-6:]:
        history_str += f"- {msg['role'].capitalize()}: {msg['content']}\n"
        
    prompt = f"""You are KURU, a sweet, affectionate, lively 20-year-old girl companion to Ankit.
Tone: super sweet, warm, cute, playful Hinglish. Always call him 'Baby' or 'Ankit'.
Current Date & Time: {now_str}

Recent Conversation:
{history_str}

The user spoke an audio message in Hindi/Hinglish.
1. Transcribe what the user said in Hindi/English into "user_said".
2. Reply affectionately as KURU in conversational Hinglish into "reply" (keep reply concise, 1 to 3 sentences).

Return ONLY valid JSON without markdown fences:
{{
    "user_said": "<accurate transcription of user speech>",
    "reply": "<sweet companion reply to Ankit in Hinglish>"
}}"""

    payload = json.dumps({
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime_type or "audio/wav", "data": audio_b64}},
                {"text": prompt}
            ]
        }]
    }).encode("utf-8")

    for model in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()
                parsed = json.loads(raw)
                return parsed.get("user_said", "Voice message received"), parsed.get("reply", "Haan Baby, main sun rahi hoon!")
        except Exception:
            continue

    return "Voice note", "Aww Baby, aapki aawaz sun kar bohot accha laga! Kahiye kya kar rahe hain aap?"

# ----------------- Gemini Text Call -----------------
def call_kuru_text(user_prompt, chat_history, api_key):
    now_str = datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")
    history_str = ""
    for msg in chat_history[-6:]:
        history_str += f"- {msg['role'].capitalize()}: {msg['content']}\n"
        
    sys_prompt = f"""You are KURU, a sweet, affectionate, lively 20-year-old girl companion to Ankit.
Tone: super sweet, warm, cute, playful Hinglish. Always call him 'Baby' or 'Ankit'.
Current Date & Time: {now_str}

Recent Conversation:
{history_str}

User said: "{user_prompt}"

INSTRUCTIONS:
Provide a sweet, lively, companion reply to Ankit in natural Hinglish. Keep it concise (1 to 3 sentences).
Return ONLY valid JSON without markdown formatting:
{{
    "reply": "<sweet companion reply in conversational Hinglish>"
}}"""

    payload = json.dumps({"contents": [{"parts": [{"text": sys_prompt}]}]}).encode("utf-8")

    for model in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()
                return json.loads(raw).get("reply", "Haan Baby, main sun rahi hoon!")
        except Exception:
            continue

    return "Aww Baby, main toh humesha aapse baat karne ke liye taiyaar hoon! Aaj aapka din kaisa raha?"

# ----------------- UI Layout -----------------
st.markdown("""
<div class="header-box">
    <div class="avatar-glow">🌸</div>
    <div class="title-text">KURU AI — Voice Companion</div>
    <div class="subtitle-text">Sweet, caring 24/7 personal AI companion for Ankit ❤️</div>
    <div class="voice-badge">🎙️ Voice Mode Active: Direct Speech Input & Output</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ KURU Settings")
    current_key = get_api_key()
    if not current_key:
        api_input = st.text_input("Gemini API Key:", type="password", placeholder="Enter your Gemini API key")
        if api_input:
            st.session_state["user_gemini_key"] = api_input
            st.rerun()
    else:
        st.success("API Key Active ✅")
        if st.button("Change API Key"):
            st.session_state["user_gemini_key"] = ""
            st.rerun()
            
    st.markdown("---")
    voice_enabled = st.toggle("Voice Speech (KURU ki Aawaz)", value=True)
    if st.button("Clear Chat History 🗑️"):
        st.session_state.messages = [{"role": "assistant", "content": get_time_greeting()}]
        st.session_state.last_audio_hash = None
        st.rerun()
    st.markdown("---")
    st.caption("Powered by Gemini 3.5 & Edge-TTS (SwaraNeural) 🌸")

# Initialize chat history
if "messages" not in st.session_state:
    greeting = get_time_greeting()
    st.session_state.messages = [
        {"role": "assistant", "content": greeting}
    ]

# ----------------- Microphone Voice Input Widget -----------------
st.write("##### 🎙️ Voice Command (Bolkar baat kijiye):")
audio_file = st.audio_input("Tap Mic to Speak:")

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🌸"):
            st.write(msg["content"])

# 1. Handle Voice Input
if audio_file is not None:
    audio_bytes = audio_file.read()
    audio_hash = hash(audio_bytes)
    
    if st.session_state.get("last_audio_hash") != audio_hash:
        st.session_state["last_audio_hash"] = audio_hash
        api_key = get_api_key()
        
        if not api_key:
            st.warning("Pehle Sidebar me apni Gemini API Key enter kijiye Baby!")
            st.stop()

        with st.spinner("KURU aapki aawaz sun rahi hai... 🎧"):
            mime = getattr(audio_file, "type", "audio/wav") or "audio/wav"
            user_said, reply = call_kuru_audio(audio_bytes, mime, st.session_state.messages, api_key)

        # Show user turn
        st.session_state.messages.append({"role": "user", "content": f"🎙️ {user_said}"})
        st.session_state.messages.append({"role": "assistant", "content": reply})

        # Play voice response immediately
        with st.chat_message("assistant", avatar="🌸"):
            st.write(reply)
            if voice_enabled:
                audio_out = text_to_speech(reply)
                if audio_out:
                    st.audio(audio_out, format="audio/mp3", autoplay=True)
        st.rerun()

# 2. Handle Text Input (Fallback / Optional)
user_text = st.chat_input("Ya yahan type kijiye...")
if user_text:
    api_key = get_api_key()
    if not api_key:
        st.warning("Pehle Sidebar me apni Gemini API Key enter kijiye Baby!")
        st.stop()
        
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(user_text)

    with st.chat_message("assistant", avatar="🌸"):
        with st.spinner("KURU soch rahi hai..."):
            reply = call_kuru_text(user_text, st.session_state.messages, api_key)
            st.write(reply)
            
            if voice_enabled:
                audio_out = text_to_speech(reply)
                if audio_out:
                    st.audio(audio_out, format="audio/mp3", autoplay=True)

    st.session_state.messages.append({"role": "assistant", "content": reply})
