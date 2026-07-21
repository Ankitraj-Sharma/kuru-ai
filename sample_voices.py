import asyncio
import edge_tts
import pygame
import time

pygame.mixer.init()

text_sample = "Haan Ankit! Kaisi ho? Main KURU hoon. Batao aaj kya plan hai tumhara?"

async def make_and_play(voice, pitch, rate, filename, label):
    print(f"\n--- Testing {label} ({voice}, pitch={pitch}, rate={rate}) ---")
    comm = edge_tts.Communicate(text_sample, voice, pitch=pitch, rate=rate)
    await comm.save(filename)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.05)
    pygame.mixer.music.unload()

async def main():
    # 1. Neerja Expressive (Youthful college girl Hinglish vibe)
    await make_and_play("en-IN-NeerjaExpressiveNeural", "+4Hz", "+5%", "v_neerja.mp3", "Style 1: Neerja Expressive (Young & Cheerful)")
    time.sleep(1)
    
    # 2. Swara with higher youthful pitch (+15Hz, +8%)
    await make_and_play("hi-IN-SwaraNeural", "+15Hz", "+8%", "v_swara_cute.mp3", "Style 2: Swara Youthful (+15Hz Sweet Girl)")
    time.sleep(1)

    # 3. Swara with +20Hz (Very sweet & bubbly)
    await make_and_play("hi-IN-SwaraNeural", "+22Hz", "+10%", "v_swara_sweet20.mp3", "Style 3: Swara 20-year-old Girl (+22Hz Bubbly)")

if __name__ == "__main__":
    asyncio.run(main())
