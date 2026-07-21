import sounddevice as sd
import numpy as np
import time

def record_until_silence(sample_rate=16000, silence_timeout=0.9, max_duration=7.0):
    """Listens until user finishes speaking, then returns audio immediately."""
    print("[*] Listening for speech (auto-stops when you stop talking)...")
    chunk_duration = 0.1 # 100ms chunks
    chunk_samples = int(sample_rate * chunk_duration)
    
    frames = []
    has_spoken = False
    silence_start = None
    start_time = time.time()
    
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
        while True:
            data, _ = stream.read(chunk_samples)
            frames.append(data)
            vol = np.abs(data).mean()
            
            # Speech detection threshold
            if vol > 120:
                has_spoken = True
                silence_start = None
            elif has_spoken:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= silence_timeout:
                    print(f"[*] Speech ended (detected {silence_timeout}s silence). Stopping recording!")
                    break
                    
            if time.time() - start_time > max_duration:
                print("[*] Max duration reached.")
                break
                
    if frames:
        return np.concatenate(frames, axis=0)
    return np.array([], dtype='int16')

if __name__ == "__main__":
    audio = record_until_silence()
    print(f"Recorded {len(audio)/16000:.2f} seconds of audio!")
