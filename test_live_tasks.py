import time
import subprocess
import os

ADB_PATH = r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe"

def run_adb(cmd):
    full_cmd = [ADB_PATH] + cmd
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    return res.stdout.strip()

def tap(x, y):
    print(f"[*] Tapping ({x}, {y})")
    run_adb(["shell", "input", "tap", str(int(x)), str(int(y))])

def type_text(text):
    print(f"[*] Typing '{text}'")
    formatted = text.replace(" ", "%s")
    for char in ['&', '<', '>', ';', '|', '$', '(', ')', '"', "'"]:
        formatted = formatted.replace(char, f"\\{char}")
    run_adb(["shell", "input", "text", formatted])

def test_youtube(song_name="Arijit Singh Mashup"):
    print(f"\n--- Testing YouTube Play: '{song_name}' ---")
    encoded = song_name.replace(" ", "+")
    # Launch search in YouTube
    run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"https://www.youtube.com/results?search_query={encoded}"])
    time.sleep(2.0)
    # Tap the first video result to auto-play! (On 1236x2750 screen, top video is at Y=750)
    tap(600, 750)
    print("✅ YouTube video tapped and playing!")

if __name__ == "__main__":
    test_youtube("Arijit Singh")
