import time
import subprocess
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ADB_PATH = r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe"

def run_adb(cmd):
    full_cmd = [ADB_PATH] + cmd
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    return res.stdout.strip()

def tap(x, y):
    print(f"[*] Tapping ({x}, {y})")
    run_adb(["shell", "input", "tap", str(int(x)), str(int(y))])

def type_text(text):
    print(f"[*] Typing: '{text}'")
    formatted = text.replace(" ", "%s")
    for char in ['&', '<', '>', ';', '|', '$', '(', ')', '"', "'"]:
        formatted = formatted.replace(char, f"\\{char}")
    run_adb(["shell", "input", "text", formatted])

def send_whatsapp(contact="MilkCake", msg="Hello from KURU"):
    print(f"\n[*] Testing WhatsApp message to '{contact}'...")
    # 1. Wake & return home
    run_adb(["shell", "input", "keyevent", "3"])
    time.sleep(0.5)

    # 2. Open WhatsApp
    run_adb(["shell", "monkey", "-p", "com.whatsapp", "-c", "android.intent.category.LAUNCHER", "1"])
    time.sleep(1.2)

    # 3. Tap search bar (618, 404)
    tap(618, 404)
    time.sleep(0.6)

    # 4. Type contact name
    type_text(contact)
    time.sleep(1.0)

    # 5. Tap top result
    tap(500, 600)
    time.sleep(1.0)

    # 6. Type message
    type_text(msg)
    time.sleep(0.6)

    # 7. Tap send button (1140, 2600)
    tap(1140, 2600)
    time.sleep(0.5)
    print("[*] WhatsApp message dispatched!")

if __name__ == "__main__":
    send_whatsapp("MilkCake", "Hello! Testing KURU AI Assistant")
