import asyncio
import edge_tts

async def generate_cache():
    # Seerat Ain Alam - Dil Ibadat soft melody style
    text = "Haan Baby... bolo na?"
    comm = edge_tts.Communicate(text, "hi-IN-SwaraNeural", pitch="+12Hz", rate="-4%")
    await comm.save("yes_ankit.mp3")
    print("Cached yes_ankit.mp3 in Seerat Ain Alam (Dil Ibadat) acoustic tone!")

if __name__ == "__main__":
    asyncio.run(generate_cache())
