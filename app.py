import os
import re
import json
import asyncio
import datetime
import urllib.request
import streamlit as st

# ========================================================
# 🌸 KURU AI — LIVE WEB VOICE COMPANION 🌸
# Deployable on Streamlit Cloud / HuggingFace Spaces
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
        padding: 24px 10px;
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.15), rgba(168, 85, 247, 0.1));
        border: 1px solid rgba(244, 114, 182, 0.25);
        border-radius: 20px;
        backdrop-filter: blur(10px);
        margin-bottom: 25px;
        box-shadow: 0 8px 32px rgba(236, 72, 153, 0.15);
    }
    
    .avatar-glow {
        width: 90px;
        height: 90px;
        margin: 0 auto 12px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ec4899, #8b5cf6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 42px;
        box-shadow: 0 0 25px rgba(236, 72, 153, 0.6);
        animation: pulse 3s infinite alternate;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 20px rgba(236, 72, 153, 0.5); }
        100% { transform: scale(1.06); box-shadow: 0 0 35px rgba(236, 72, 153, 0.85); }
    }
    
    .title-text {
        font-size: 26px;
        font-weight: 700;
        background: linear-gradient(to right, #f472b6, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    
    .subtitle-text {
        color: #fbcfe8;
        font-size: 14px;
        opacity: 0.9;
    }
    
    .stChatMessage {
        border-radius: 16px;
        padding: 12px 16px;
        margin-bottom: 12px;
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(244, 114, 182, 0.15);
    }
    
    .stChatInputContainer {
        border-radius: 25px !important;
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
    # 1. Check Streamlit secrets
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    # 2. Check environment variable
    if os.getenv("GEMINI_API_KEY"):
        return os.getenv("GEMINI_API_KEY")
    # 3. Check session state (manual entry)
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
    # Clean text of markdown/emojis
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

# ----------------- Gemini API Call -----------------
def call_kuru_gemini(user_prompt, chat_history, api_key):
    now_str = datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")
    
    # Format recent history
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
Provide a sweet, lively, companion reply to Ankit in natural Hinglish. Keep it concise (1 to 3 sentences) so it speaks beautifully.
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
</div>
""", unsafe_allow_html=True)

# Sidebar for settings & API key
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
    voice_enabled = st.toggle("Voice Speech (Aawaz)", value=True)
    st.markdown("---")
    st.caption("Powered by Gemini 3.5 & Edge-TTS (SwaraNeural) 🌸")

# Initialize chat history
if "messages" not in st.session_state:
    greeting = get_time_greeting()
    st.session_state.messages = [
        {"role": "assistant", "content": greeting}
    ]

# Display chat messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💻"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🌸"):
            st.write(msg["content"])

# User Chat Input
user_input = st.chat_input("KURU se baat kijiye... (e.g. Kaisa chal raha hai Baby?)")

if user_input:
    api_key = get_api_key()
    if not api_key:
        st.warning("Pehle Sidebar me apni Gemini API Key enter kijiye Baby!")
        st.stop()
        
    # Append & display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(user_input)

    # Generate reply
    with st.chat_message("assistant", avatar="🌸"):
        with st.spinner("KURU soch rahi hai..."):
            reply = call_kuru_gemini(user_input, st.session_state.messages, api_key)
            st.write(reply)
            
            # Generate and play natural audio speech
            if voice_enabled:
                audio_data = text_to_speech(reply)
                if audio_data:
                    st.audio(audio_data, format="audio/mp3", autoplay=True)

    st.session_state.messages.append({"role": "assistant", "content": reply})
