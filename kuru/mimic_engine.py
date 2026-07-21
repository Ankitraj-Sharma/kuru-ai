import json
from google import genai
from google.genai import types
from kuru.config import GEMINI_MODEL

class MimicEngine:
    def __init__(self, gemini_client, memory):
        self.client = gemini_client
        self.memory = memory

    def analyze_and_learn_chat_style(self, contact_name, sample_user_messages):
        """Analyzes how the user talks to this contact and saves their tone."""
        if not self.client or not sample_user_messages:
            return

        prompt = f"""You are analyzing the user's personal chatting style for contact: "{contact_name}".
Here are some sample messages sent by the user:
{sample_user_messages}

Extract:
1. Slang/Keywords frequently used (e.g., 'bhai', 'bro', 'hnn', 'yaar', 'yr', 'arre')
2. Sentence length (short, medium, paragraphs)
3. Language style (Hinglish, pure Hindi, English, emojis used)
4. Overall tone (casual friend, polite elder, professional, funny)

Return a concise summary of the user's style to mimic them perfectly.
Format: JSON with key "mimic_profile"."""

        try:
            resp = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            data = json.loads(resp.text)
            profile = data.get("mimic_profile", str(resp.text))
            self.memory.save_fact("chat_style", f"style_with_{contact_name.lower()}", json.dumps(profile) if isinstance(profile, dict) else str(profile))
            print(f"[Mimic Engine] Learned chatting style for {contact_name}!")
        except Exception as e:
            print(f"Warning in learning chat style: {e}")

    def generate_chat_reply(self, contact_name, chat_context_on_screen, incoming_message):
        """Generates a reply mimicking the user's texting style."""
        if not self.client:
            return "Hnn theek h"

        facts = self.memory.get_all_facts()
        style_info = ""
        for f in facts:
            if f["key"] == f"style_with_{contact_name.lower()}":
                style_info = f"Known style for {contact_name}: {f['value']}"
                break

        prompt = f"""You are impersonating the USER on WhatsApp. You must reply to "{contact_name}" in the exact same way the USER texts.
DO NOT sound like an AI assistant. DO NOT use formal robot language.

Recent Chat Context on Screen:
{chat_context_on_screen}

Incoming Message from {contact_name}: "{incoming_message}"
{style_info}

Rules:
- Write in natural, realistic Hinglish (e.g., "hnn bhai bol", "acha theek h", "kya chal rha", etc.).
- Use the exact same vibe, slang, and capitalization/spelling patterns as real chat.
- Keep it concise and natural, just like the user typing on a phone.

Return ONLY the message text to be sent, nothing else."""

        try:
            resp = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt]
            )
            reply = resp.text.strip().strip('"').strip("'")
            return reply
        except Exception as e:
            return "Hnn theek h bhai"

    def generate_call_response(self, caller_name, what_caller_said, user_status="busy"):
        """Generates natural spoken replies as the user during phone calls."""
        if not self.client:
            return "Haan bhai, abhi thoda busy tha, thodi der me call karta hoon."

        prompt = f"""You are the USER himself talking on a phone call.
Caller: "{caller_name}"
What caller said: "{what_caller_said}"
Your current status: {user_status}

Rules:
- Speak in natural Indian Hindi/Hinglish male tone (e.g. "Haan bhai", "Arre kya haal hai", "Bol na", "Haan theek hai").
- Keep it short, conversational (1-2 sentences max), sound completely human.
- DO NOT say you are an AI. You ARE the user.

Return ONLY what to speak out loud."""

        try:
            resp = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt]
            )
            return resp.text.strip().strip('"')
        except Exception as e:
            return "Haan bhai, thoda busy tha, bol kya hua?"
