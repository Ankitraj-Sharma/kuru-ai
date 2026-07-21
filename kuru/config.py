import os
from dotenv import load_dotenv

load_dotenv()

ADB_PATH = os.getenv("ADB_PATH", r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Voice Profiles
# 1. Hindi/Hinglish: Seerat Ain Alam style (Dil Ibadat cover) - soft, melodic, gentle cadence
KURU_VOICE_HINDI = os.getenv("KURU_VOICE_HINDI", "hi-IN-SwaraNeural")
KURU_PITCH_HINDI = "+12Hz"
KURU_RATE_HINDI = "-4%"

# 2. English: Selena Gomez style (We Don't Talk Anymore) - breathy, intimate, whisper-pop
KURU_VOICE_ENGLISH = os.getenv("KURU_VOICE_ENGLISH", "en-US-AvaNeural")
KURU_PITCH_ENGLISH = "+0Hz"
KURU_RATE_ENGLISH = "-3%"

# Default fallback
KURU_VOICE_FEMALE = KURU_VOICE_HINDI

# User Proxy: Realistic Indian Male voice to mimic the user during calls
USER_VOICE_MALE = os.getenv("USER_VOICE_MALE", "hi-IN-MadhurNeural")
USER_PITCH_MALE = "+0Hz"
USER_RATE_MALE = "+0%"

GEMINI_MODEL = "gemini-3.5-flash-lite"

APP_PACKAGES = {
    "whatsapp": "com.whatsapp",
    "chrome": "com.android.chrome",
    "youtube": "com.google.android.youtube",
    "gmail": "com.google.android.gm",
    "mail": "com.google.android.gm",
    "email": "com.google.android.gm",
    "settings": "com.android.settings",
    "camera": "com.android.camera2",
    "dialer": "com.google.android.dialer",
    "phone": "com.google.android.dialer",
    "messages": "com.google.android.apps.messaging",
    "sms": "com.google.android.apps.messaging",
    "maps": "com.google.android.apps.maps",
    "clock": "com.android.deskclock",
    "alarm": "com.android.deskclock",
    "calculator": "com.miui.calculator",
    "notes": "com.miui.notes",
    "calendar": "com.xiaomi.calendar",
    "instagram": "com.instagram.android",
    "spotify": "com.spotify.music",
    "telegram": "org.telegram.messenger",
    "snapchat": "com.snapchat.android",
    "paytm": "net.one97.paytm",
    "phonepe": "com.phonepe.app",
    "playstore": "com.android.vending",
    "photos": "com.google.android.apps.photos",
    "gallery": "com.miui.gallery"
}
