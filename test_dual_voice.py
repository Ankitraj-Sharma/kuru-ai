import sys
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from kuru.voice_engine import VoiceEngine
import time

def test_voices():
    ve = VoiceEngine()
    print("Testing KURU's Female Voice...")
    ve.speak("नमस्ते सर, मैं कुरु हूँ। आपकी पर्सनल फीमेल एआई असिस्टेंट। मैं आपके सारे काम संभालूँगी।", as_user=False)
    
    time.sleep(1)
    
    print("Testing User's Mimic Male Voice for Calls...")
    ve.speak("हाँ भाई, मैं अभी थोड़ा बिजी था। बोल क्या बात है, सब ठीक?", as_user=True)

if __name__ == "__main__":
    test_voices()
