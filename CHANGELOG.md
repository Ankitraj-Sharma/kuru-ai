# KURU AI - Development History

- `2026-07-21T11:14:30`: feat: initialize project workspace and environment setup
- `2026-07-21T22:14:02`: chore: configure gitignore rules for media and logs
- `2026-07-22T09:13:34`: feat: implement base entrypoint main.py
- `2026-07-22T20:13:06`: feat: add termux integration shell script kuru.sh
- `2026-07-23T07:12:38`: feat: setup speech recognition interface with termux-speech-to-text
- `2026-07-23T18:12:10`: feat: configure termux-tts-speak audio synthesizer
- `2026-07-24T05:11:42`: perf: tune voice pitch to 1.25 and speech rate to 0.95 for natural timbre
- `2026-07-24T16:11:14`: feat: add Gemini API client with fallback endpoints
- `2026-07-25T03:10:46`: fix: handle HTTP 503 and network timeouts during API calls
- `2026-07-25T14:10:18`: feat: add support for gemini-3.5-flash-lite low latency model
- `2026-07-26T01:09:50`: feat: add model fallback cascade for reliability
- `2026-07-26T12:09:22`: feat: introduce SQLite database for persistent user context
- `2026-07-26T23:08:54`: feat: create user_facts schema for category key value storage
- `2026-07-27T10:08:26`: feat: implement get_memory_context query with limit sorting
- `2026-07-27T21:07:58`: feat: implement auto-learning fact extraction from user conversations
- `2026-07-28T08:07:30`: feat: add dynamic time-aware greeting generator
- `2026-07-28T19:07:02`: feat: add morning greeting handler (05:00 - 12:00)
