import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from dotenv import load_dotenv, set_key
load_dotenv()

from kuru.brain import KuruBrain

def setup_env():
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("\n" + "="*50)
        print("KEY NEEDED: GEMINI_API_KEY")
        print("Google AI Studio: https://aistudio.google.com/app/apikey")
        print("="*50)
        user_key = input("API Key paste kijiye: ").strip()
        if user_key:
            if not os.path.exists(env_file):
                with open(env_file, "w") as f:
                    f.write(f"GEMINI_API_KEY={user_key}\n")
            else:
                set_key(env_file, "GEMINI_API_KEY", user_key)
            os.environ["GEMINI_API_KEY"] = user_key
            print("[OK] API Key saved!\n")
            return user_key
    return api_key

def main():
    print("""
    ========================================================
        ⚡ KURU - Autonomous AI Companion & Assistant ⚡
        (Wake-Word: 'KURU' | Continuous Chat | Phone Control)
    ========================================================
    """)
    
    api_key = setup_env()
    kuru = KuruBrain()
    if api_key:
        kuru.set_api_key(api_key)

    # Sweet 20-year-old girl welcome
    welcome_msg = "Haan Ankit! Main KURU hoon. Batao aaj kya plan hai tumhara?"
    kuru.voice.speak(welcome_msg, as_user=False)

    print("\n[WAKE-WORD MODE ACTIVE]")
    print("[*] Boliye: 'KURU' ya 'Hey KURU'")
    print("[*] Continuous Chat: Ek baar jagane ke baad aap lagatar baat kar sakte hain!\n")

    while True:
        try:
            # Standby listening for Wake-Word 'KURU'
            activated = kuru.voice.wait_for_wakeword()
            if not activated:
                break

            # Continuous Conversation Loop
            consecutive_silence = 0
            while True:
                # Listen to user's question or follow-up
                prompt = "Boliye Ankit, main sun rahi hoon..." if consecutive_silence == 0 else "Aap aage bol sakte hain..."
                command = kuru.voice.listen(prompt_text=prompt)

                if not command:
                    consecutive_silence += 1
                    if consecutive_silence >= 1:
                        # User is done talking for now, go back to standby
                        print("[*] [Standby mode me wapas jaa rahi hoon. Jab bhi kaam ho 'KURU' boliyega]")
                        break
                    continue

                consecutive_silence = 0 # Reset silence counter

                if command.lower() in ["exit", "quit", "bye", "alvida", "stop", "chalo theek h"]:
                    kuru.voice.speak("Alvida Ankit, apna khayal rakhna!", as_user=False)
                    break

                # Process command / answer question / execute phone task
                kuru.process_command(command)

        except KeyboardInterrupt:
            print("\nExiting KURU...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
