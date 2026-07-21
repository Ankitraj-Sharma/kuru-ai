import asyncio
import edge_tts
import pygame
import time

pygame.mixer.init()

async def play_voice(text, voice, pitch, rate, filename, title):
    print(f"\n[*] Generating {title}...")
    comm = edge_tts.Communicate(text, voice, pitch=pitch, rate=rate)
    await comm.save(filename)
    print(f"[*] Playing {title}...")
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.04)
    pygame.mixer.music.unload()

async def test_clones():
    # 1. Hindi Profile (Seerat Ain Alam - Dil Ibadat style)
    # Characteristics: Soft, gentle, melodic, relaxing cadence, warm
    hindi_text = "Haan Baby... main tumhari KURU hoon. Batao aaj tumhara mood kaisa hai? Main hamesha tumhare saath hoon."
    await play_voice(hindi_text, "hi-IN-SwaraNeural", "+12Hz", "-4%", "seerat_hindi_kuru.mp3", "Hindi (Seerat Ain Alam - Dil Ibadat Style)")
    time.sleep(1)

    # 2. English Profile (Selena Gomez - We Don't Talk Anymore style)
    # Characteristics: Breathy, intimate, soft whisper-pop, gentle tone
    english_text = "Hey Baby... I'm right here for you. Just tell me what you need, and I'll take care of it."
    await play_voice(english_text, "en-US-AvaNeural", "+0Hz", "-3%", "selena_english_kuru.mp3", "English (Selena Gomez - We Don't Talk Anymore Style)")

if __name__ == "__main__":
    asyncio.run(test_clones())
