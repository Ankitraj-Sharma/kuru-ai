# ⚡ KURU - Autonomous AI Phone Assistant (Jarvis-style)

KURU is an autonomous AI assistant powered by **Google Gemini 2.5 Flash**, **Vision Agent UI Navigation (AppAgent)**, **Edge-TTS**, and **Android ADB Controller**.

## 🌟 Key Features

1. **True Jarvis UI Control (AppAgent Architecture)**:
   - Takes real-time screenshots and dumps Android UI layout XML (`uiautomator`).
   - Uses Gemini Multimodal Vision to find buttons, search bars, and input fields.
   - Automatically taps, types, swipes, and navigates apps (WhatsApp, Chrome, YouTube, Gmail, etc.).

2. **Natural Voice Interaction**:
   - Ultra-realistic natural voice responses powered by Microsoft Edge Neural TTS (`hi-IN-MadhurNeural`).
   - Friendly conversational Hindi/Hinglish speaking style like a trusted friend.
   - Speech-to-Text input from PC microphone.

3. **Self-Learning Long-Term Memory**:
   - Stores user preferences, friends' birthdays, daily habits, and frequent app actions in a persistent SQLite database (`kuru_memory.db`).
   - Improves its responses and execution over time.

---

## 🚀 How to Run

1. Open Terminal / PowerShell in `d:\personal AI`.
2. Activate Virtual Environment:
   ```powershell
   .\venv\Scripts\activate
   ```
3. Run KURU:
   ```powershell
   python main.py
   ```
4. Enter your Gemini API Key when prompted (or save it inside `.env`).

---

## 📁 Project Structure

```
d:\personal AI\
├── kuru\
│   ├── config.py           # Configuration (ADB path, voice models, packages)
│   ├── phone_controller.py # ADB Bridge (tap, type, swipe, screencap, xml dump)
│   ├── vision_agent.py     # Gemini Vision model to plan UI actions
│   ├── voice_engine.py     # Edge-TTS voice synthesis & mic listener
│   ├── memory.py           # Self-learning SQLite memory database
│   └── brain.py            # Central coordinator & Jarvis agent
├── test_adb.py             # Script to verify phone connection & screenshot
├── test_voice.py           # Script to test Hindi TTS voice
├── main.py                 # Main application loop
└── README.md
```
