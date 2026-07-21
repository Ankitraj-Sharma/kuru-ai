import os
import uuid
import asyncio
import subprocess
import edge_tts

async def speak_test(text):
    unique_name = f"voice_{uuid.uuid4().hex[:6]}.mp3"
    abs_path = os.path.abspath(unique_name)
    comm = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await comm.save(abs_path)
    print(f"Generated {abs_path}")
    
    ps_cmd = f'''
    Add-Type -AssemblyName presentationCore
    $player = New-Object System.Windows.Media.MediaPlayer
    $player.Open([System.Uri]"{abs_path}")
    Start-Sleep -Milliseconds 250
    $player.Play()
    Start-Sleep -Seconds 3
    $player.Close()
    '''
    subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
    try:
        os.remove(abs_path)
        print("Cleaned up audio file.")
    except Exception as e:
        print(f"Cleanup note: {e}")

if __name__ == "__main__":
    asyncio.run(speak_test("नमस्ते अंकित, मैं एकदम तैयार हूँ।"))
    asyncio.run(speak_test("दूसरी बार बोलने में भी कोई एरर नहीं आएगा।"))
