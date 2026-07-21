import asyncio
import os
import io
import time
import uuid
import wave
import json
import re
import queue
import edge_tts
import speech_recognition as sr
import sounddevice as sd
import numpy as np
import vosk
import pygame
from kuru.config import (
    KURU_VOICE_HINDI, KURU_PITCH_HINDI, KURU_RATE_HINDI,
    KURU_VOICE_ENGLISH, KURU_PITCH_ENGLISH, KURU_RATE_ENGLISH,
    USER_VOICE_MALE, USER_PITCH_MALE, USER_RATE_MALE
)

HINDI_GRAMMAR_WORDS = {
    'haan', 'nahi', 'nhi', 'kr', 'kar', 'karo', 'kare', 'karegi', 'karunga', 'karungi',
    'karta', 'karti', 'raha', 'rhi', 'rha', 'rahe', 'hoon', 'hu', 'hai', 'hain', 'batao',
    'bataye', 'bolo', 'boliye', 'suno', 'meri', 'mere', 'mera', 'tum', 'tumhara', 'tumhari',
    'aap', 'aapka', 'aapki', 'kaise', 'kaisa', 'kaisi', 'kya', 'kyu', 'kyun', 'abhi', 'avi',
    'theek', 'thik', 'accha', 'achha', 'acha', 'achhi', 'achhe', 'bhej', 'diya', 'diye',
    'gana', 'gane', 'chala', 'chalana', 'chalaye', 'dekho', 'kuch', 'kuchh', 'bahot', 'bohot',
    'kripya', 'bhai', 'yaar', 'yrr'
}

class VoiceEngine:
    def __init__(self, male_voice=USER_VOICE_MALE):
        self.male_voice = male_voice
        self.recognizer = sr.Recognizer()
        self.sample_rate = 16000
        
        # Initialize pygame mixer for ultra-fast audio playback (Zero delay!)
        pygame.mixer.init()

        # Load local fast offline Vosk model
        vosk.SetLogLevel(-1)
        print("[*] Loading offline Real-time Wake-Word Engine...")
        self.vosk_model = vosk.Model(lang="en-us")
        print("[OK] Wake-Word Engine Ready (Instant Local Detection)!")

    def detect_language(self, text):
        """Identifies whether text should be spoken in Hindi (Seerat profile) or English (Selena profile)."""
        if re.search(r'[\u0900-\u097F]', text):
            return 'hi'
        words = re.findall(r'[a-zA-Z]+', text.lower())
        if not words:
            return 'hi'
        hindi_matches = sum(1 for w in words if w in HINDI_GRAMMAR_WORDS)
        if hindi_matches >= 1:
            return 'hi'
        return 'en'

    def play_sound(self, file_path):
        """Plays audio instantly with pygame (0.01 sec latency)."""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.04)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"(Play warning: {e})")

    async def _generate_audio(self, text, as_user, output_file):
        if as_user:
            voice = self.male_voice
            pitch = USER_PITCH_MALE
            rate = USER_RATE_MALE
        else:
            lang = self.detect_language(text)
            if lang == "en":
                # Selena Gomez style: breathy, intimate, whisper-pop
                voice = KURU_VOICE_ENGLISH
                pitch = KURU_PITCH_ENGLISH
                rate = KURU_RATE_ENGLISH
            else:
                # Seerat Ain Alam style: soft, melodic, gentle cadence
                voice = KURU_VOICE_HINDI
                pitch = KURU_PITCH_HINDI
                rate = KURU_RATE_HINDI

        comm = edge_tts.Communicate(text, voice, pitch=pitch, rate=rate)
        await comm.save(output_file)

    def speak(self, text, as_user=False):
        if as_user:
            speaker_label = "[YOU (Mimic Mode)]"
        else:
            lang = self.detect_language(text)
            speaker_label = "[KURU (Selena Gomez - English)]" if lang == "en" else "[KURU (Seerat Ain Alam - Hindi)]"

        try:
            print(f"\n{speaker_label}: {text}")
        except Exception:
            print(f"\n{speaker_label}: (Speaking...)")

        unique_file = os.path.abspath(f"voice_{uuid.uuid4().hex[:6]}.mp3")
        try:
            asyncio.run(self._generate_audio(text, as_user, unique_file))
            self.play_sound(unique_file)
        except Exception as e:
            print(f"(Voice error: {e})")
        finally:
            if os.path.exists(unique_file):
                try:
                    os.remove(unique_file)
                except Exception:
                    pass

    def record_until_silence(self, silence_timeout=3.5, max_duration=20.0):
        """Patient listening: Never cuts you off! Waits for 3.5s of pure silence after you finish speaking."""
        chunk_samples = int(self.sample_rate * 0.1) # 100ms
        frames = []
        has_spoken = False
        silence_start = None
        start_time = time.time()
        
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16') as stream:
            while True:
                data, _ = stream.read(chunk_samples)
                frames.append(data)
                vol = np.abs(data).mean()
                
                # Soft speech detection (sensitive)
                if vol > 50:
                    has_spoken = True
                    silence_start = None
                elif has_spoken:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start >= silence_timeout:
                        # Full sentence definitely completed!
                        break
                        
                # If user hasn't said a word for 7 seconds after prompt, exit
                if not has_spoken and time.time() - start_time > 7.0:
                    break
                    
                if time.time() - start_time > max_duration:
                    break
                    
        if frames and has_spoken:
            return np.concatenate(frames, axis=0)
        return np.array([], dtype='int16')

    def audio_to_text(self, audio_np):
        """High-accuracy Speech-to-Text on full spoken audio."""
        if len(audio_np) == 0 or np.abs(audio_np).max() < 100:
            return None

        byte_io = io.BytesIO()
        with wave.open(byte_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_np.tobytes())
        byte_io.seek(0)

        with sr.AudioFile(byte_io) as source:
            audio_data = self.recognizer.record(source)
            # Try Hindi first (best for Indian Hinglish & native Hindi)
            try:
                text = self.recognizer.recognize_google(audio_data, language="hi-IN")
                if text:
                    return text.strip()
            except Exception:
                pass

            # Fallback to Indian English
            try:
                text = self.recognizer.recognize_google(audio_data, language="en-IN")
                if text:
                    return text.strip()
            except Exception:
                pass

        return None

    def listen(self, prompt_text="Boliye Ankit, main sun rahi hoon..."):
        print(f"\n[*] {prompt_text}")
        print("[*] [Listening...] (Puri baat aaram se boliye)")
        audio_np = self.record_until_silence()
        text = self.audio_to_text(audio_np)
        if text:
            print(f"[You]: '{text}'")
            return text
        else:
            return None

    def wait_for_wakeword(self):
        """Real-time instant local wake word detection using Vosk."""
        q = queue.Queue()

        def audio_callback(indata, frames, time_info, status):
            q.put(bytes(indata))

        rec = vosk.KaldiRecognizer(self.vosk_model, self.sample_rate)
        wake_words = ["kuru", "guru", "crew", "kru", "kuro", "kroo", "hey kuru", "he kuru"]

        print("\n" + "="*50)
        print("[KURU Standby] Boliye: 'KURU' ya 'Hey KURU'")
        print("="*50)

        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=4000, dtype='int16',
                               channels=1, callback=audio_callback):
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    text = res.get("text", "").lower()
                    if text:
                        print(f"Heard: '{text}'", end="\r", flush=True)
                        for w in wake_words:
                            if w in text:
                                print(f"\n[WAKE-WORD DETECTED]: Matched '{w}' -> KURU Awake!")
                                if os.path.exists("yes_ankit.mp3"):
                                    self.play_sound("yes_ankit.mp3")
                                else:
                                    self.speak("Haan Baby... bolo na?", as_user=False)
                                return True
                else:
                    partial = json.loads(rec.PartialResult()).get("partial", "").lower()
                    if partial:
                        for w in wake_words:
                            if w in partial:
                                print(f"\n[INSTANT WAKE-WORD]: Matched '{w}' -> KURU Awake!")
                                if os.path.exists("yes_ankit.mp3"):
                                    self.play_sound("yes_ankit.mp3")
                                else:
                                    self.speak("Haan Baby... bolo na?", as_user=False)
                                return True
