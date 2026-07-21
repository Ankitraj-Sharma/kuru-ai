import sounddevice as sd
import numpy as np
import wave
import io
import speech_recognition as sr

r = sr.Recognizer()
sample_rate = 16000
duration = 4

print("="*50)
print("🎙️ MICROPHONE TEST: 4 seconds ke liye 'KURU' boliye...")
print("="*50)

rec = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
sd.wait()

vol = np.abs(rec).mean()
peak = np.abs(rec).max()
print(f"📊 Audio Volume Level: Mean = {vol:.1f}, Peak = {peak}")

if peak < 100:
    print("⚠️ Warning: Mic se bilkul aawaz nahi aayi! (Check mic mute or volume)")
else:
    byte_io = io.BytesIO()
    with wave.open(byte_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(rec.tobytes())
    byte_io.seek(0)

    with sr.AudioFile(byte_io) as source:
        audio = r.record(source)
        try:
            text_hi = r.recognize_google(audio, language="hi-IN")
            print(f"🗣️ Google STT (Hindi) heard: '{text_hi}'")
        except Exception as e:
            print(f"Hindi recognition error: {e}")

        try:
            text_en = r.recognize_google(audio, language="en-IN")
            print(f"🗣️ Google STT (English) heard: '{text_en}'")
        except Exception as e:
            print(f"English recognition error: {e}")
