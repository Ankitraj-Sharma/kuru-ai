import subprocess
import os

ADB_PATH = r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe"

def run_adb(cmd):
    full_cmd = [ADB_PATH] + cmd
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    return res.stdout.strip()

def get_screen_size():
    output = run_adb(["shell", "wm", "size"])
    print(f"Screen Size Output: {output}")
    # e.g., Physical size: 1236x2750
    for line in output.splitlines():
        if "Physical size:" in line:
            parts = line.split(":")[-1].strip().split("x")
            return int(parts[0]), int(parts[1])
    return 1080, 2400

def capture_screenshot(output_path="test_screen.png"):
    cmd = [ADB_PATH, "exec-out", "screencap", "-p"]
    with open(output_path, "wb") as f:
        subprocess.run(cmd, stdout=f)
    print(f"Screenshot saved to: {output_path} (size: {os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    w, h = get_screen_size()
    print(f"Detected Screen Resolution: {w}x{h}")
    capture_screenshot("test_screen.png")
