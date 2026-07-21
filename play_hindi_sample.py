import asyncio
import edge_tts
import pygame
import time

pygame.mixer.init()

async def play_seerat():
    text = "Haan Baby... main tumhari KURU hoon. Batao aaj tumhara mood kaisa hai? Main hamesha tumhare saath hoon, jo bologe sab karungi!"
    print("\n[*] Playing Seerat Ain Alam (Dil Ibadat) Acoustic Hindi Profile...")
    comm = edge_tts.Communicate(text, "hi-IN-SwaraNeural", pitch="+12Hz", rate="-4%")
    await comm.save("test_seerat_now.mp3")
    
    pygame.mixer.music.load("test_seerat_now.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.04)
    pygame.mixer.music.unload()
    print("[OK] Done!")

if __name__ == "__main__":
    asyncio.run(play_seerat())
