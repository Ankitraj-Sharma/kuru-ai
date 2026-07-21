import asyncio
import edge_tts
import pygame
import time

pygame.mixer.init()

async def gen_and_play(voice, text, name):
    comm = edge_tts.Communicate(text, voice, pitch="+2Hz")
    await comm.save(f"{name}.mp3")
    print(f"Playing {name} ({voice})...")
    pygame.mixer.music.load(f"{name}.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.05)
    pygame.mixer.music.unload()

async def main():
    text = "Haan Ankit! Main KURU hoon. Main hamesha tumhari help ke liye yahan hoon, batao kya help chahiye?"
    # Test 1: Expressive Neerja
    await gen_and_play("en-IN-NeerjaExpressiveNeural", text, "test_neerja")
    time.sleep(1)
    # Test 2: Sweet Swara
    await gen_and_play("hi-IN-SwaraNeural", text, "test_swara")

if __name__ == "__main__":
    asyncio.run(main())
