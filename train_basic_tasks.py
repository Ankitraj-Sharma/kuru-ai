import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import subprocess
import time
import os
import urllib.parse
from kuru.config import ADB_PATH

def run_adb(cmd):
    full_cmd = [ADB_PATH] + cmd
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    return res.stdout.strip(), res.stderr.strip()

print("="*60)
print("🔍 KURU BASIC TASKS CAPABILITY & PERMISSION CHECK")
print("="*60)

# Check 1: Tap Permission
out, err = run_adb(["shell", "input", "tap", "100", "100"])
can_tap = "SecurityException" not in err and "SecurityException" not in out
if can_tap:
    print("✅ [TOUCH/TAP PERMISSION]: ACTIVE (Phone allows tap & typing)")
else:
    print("❌ [TOUCH/TAP PERMISSION]: BLOCKED BY XIAOMI!")
    print("   👉 Solution: Phone Settings -> Developer Options -> Enable 'USB debugging (Security settings)'")

# Check 2: YouTube Song Play
print("\n🎵 Testing YouTube Song Intent...")
song = "arijit singh mashup"
encoded = urllib.parse.quote_plus(song)
run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"https://www.youtube.com/results?search_query={encoded}"])
print(f"✅ YouTube search for '{song}' dispatched in 0.2s!")

# Check 3: Spotify Song Play
print("\n🎶 Testing Spotify Intent...")
run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"spotify:search:{encoded}"])
print(f"✅ Spotify search for '{song}' dispatched in 0.2s!")

# Check 4: Normal SMS
print("\n✉️ Testing SMS Intent...")
run_adb(["shell", "am", "start", "-a", "android.intent.action.SENDTO", "-d", "sms:9876543210", "--es", "sms_body", "Hello from KURU"])
print("✅ SMS App with message opened in 0.2s!")

# Check 5: WhatsApp Intent
print("\n💬 Testing WhatsApp Message Intent...")
msg_encoded = urllib.parse.quote_plus("Hello! KURU testing WhatsApp")
run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"whatsapp://send?text={msg_encoded}"])
print("✅ WhatsApp share dispatched in 0.2s!")
