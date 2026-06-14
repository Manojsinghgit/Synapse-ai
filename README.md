# 🤖 Super-AI — Free Offline Voice-Controlled Assistant

**Install. Run. Talk.** That's it.

## Install (one command)

```bash
cd alright
pip install .
```

## Run (one command)

```bash
superai
```

First run auto-downloads AI models (~1.1 GB). After that, starts instantly.

Then just talk:

> **"Hey AI, open youtube"**

## What it can do

| Say this | It does this |
|----------|-------------|
| "Hey AI, **open google**" | Opens google.com in browser |
| "Hey AI, **open youtube**" | Opens youtube.com |
| "Hey AI, **launch Safari**" | Opens Safari app |
| "Hey AI, **play** /path/to/song.mp3" | Plays media file |
| "Hey AI, **send whatsapp** to +919876543210 — hello" | Automates sending WhatsApp message |
| "Hey AI, **search web** for latest AI news" | Opens Chrome & tells you the top web result |
| "Hey AI, **send message** — meeting at 5" | Sends Telegram message |
| "Hey AI, **send voice note** — I'll be late" | Sends voice note on Telegram |
| "Hey AI, **set reminder** 5 minutes — drink water" | Reminds you in 5 min |
| "Hey AI, **what is Python?**" | Answers your question by voice |
| "Hey AI, **analyse video** /path/to/clip.mp4" | Tells what's in the video |

## Telegram Setup (optional)

If you want messaging features:

1. Open Telegram → search **@BotFather** → `/newbot` → copy token
2. Search **@userinfobot** → `/start` → copy your chat ID
3. Create a `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_id
   ```

Without Telegram setup, all other features work fine.

## Requirements

- Python 3.10+
- Microphone
- 6 GB RAM (minimum)
- ~1.5 GB disk space (for AI models)
- Internet (only for first-time model download)

## How it works

```
You speak → Vosk (offline STT) → AI Brain (Llama 3.2 1B) → Action / Answer → Speaks back
```

Everything runs locally on your machine. No cloud. No API bills. No data leaves your computer.

## License

MIT
