import asyncio
import edge_tts
import subprocess
import os

VOICE = "hi-IN-MadhurNeural" # Very realistic Hindi/Hinglish voice

async def speak_text(text, filename="output.mp3"):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)
    print(f"Generated voice audio at {filename}")
    
    # Play using PowerShell MediaPlayer
    ps_cmd = f'''
    Add-Type -AssemblyName presentationCore
    $player = New-Object System.Windows.Media.MediaPlayer
    $player.Open([System.Uri]"{os.path.abspath(filename)}")
    Start-Sleep -Milliseconds 500
    $player.Play()
    Start-Sleep -Seconds 4
    $player.Stop()
    $player.Close()
    '''
    subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
    print("Finished playing audio.")

if __name__ == "__main__":
    asyncio.run(speak_text("नमस्ते सर, मैं कुरु हूँ। आपका पर्सनल एआई असिस्टेंट। मैं आपके फोन के सारे काम करने के लिए तैयार हूँ।"))
