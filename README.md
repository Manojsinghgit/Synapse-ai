# 🤖 Synapse-Assistant-AI — Free Offline Voice-Controlled Assistant

**Install. Run. Talk.** That's it. 

Synapse-Assistant-AI is a completely offline, privacy-first, voice-controlled AI assistant for your computer. It listens to your voice commands, processes them locally without sending your data to any cloud, performs desktop automation tasks, and speaks back to you.

---

## 🌟 Key Features

- **100% Offline & Private:** Uses local LLMs (via Ollama) and offline Speech-to-Text (Vosk). No API keys, no internet required (except for initial setup and web searches).
- **Voice-Controlled:** Always listening for its wake word (e.g., "Jarvis", "Friday", or your custom name).
- **Context Memory (v0.2.0):** Remembers your recent conversation history so you can ask follow-up questions naturally.
- **Vision & Clipboard (v0.2.0):** Can read your screen (OCR) and read your copied clipboard text.
- **Plugin System (v0.2.0):** Easily extend the AI's capabilities by dropping Python scripts into a plugins folder.
- **Desktop Automation:** Open websites, launch apps, play media, and search the web hands-free.
- **Smart Notifications:** Automatically notifies you via a Telegram Bot when a background task completes.
- **WhatsApp Integration:** Automates sending WhatsApp messages to your contacts.

---

## 🚀 Installation

It takes just one command to install the assistant from PyPI:

```bash
pip install synapse-assistant-ai
```

*(Note: Ensure you have Python 3.10+ installed on your system).*

---

## ⚙️ Quick Start & Setup

Run the assistant from your terminal:

```bash
synapse-ai
```
*(Alternatively, you can also use the `superai` command).*

**First-Time Interactive Setup:**
The first time you run the command, an interactive setup will start right in your terminal:
1. **Name your AI:** Choose a wake word (e.g., Jarvis, Friday, or Hey AI).
2. **Telegram Notifications (Optional):** If you want to receive task completion alerts on your phone, you will be prompted to paste your Telegram Bot Token and Chat ID directly in the terminal. **No `.env` editing required!**
3. **Model Download:** It will auto-download the necessary AI voice models (~1.1 GB, one-time only).

After that, it starts instantly. Just say your wake word:
> **"Jarvis, open youtube"**

---

## 🗣️ What it can do

Here are some examples of what you can ask your assistant to do:

| Say this | It does this |
|----------|-------------|
| **"Jarvis, open google"** | Opens google.com in your default browser |
| **"Jarvis, open youtube"** | Opens youtube.com |
| **"Jarvis, launch Safari"** | Opens the Safari application (Mac) |
| **"Jarvis, read my screen"** | Takes a screenshot and reads the text visible on your screen (OCR) |
| **"Jarvis, what's on my clipboard"** | Reads the text you currently have copied |
| **"Jarvis, play /path/to/song.mp3"** | Plays the specified media file locally |
| **"Jarvis, send whatsapp to +919876543210 — hello"** | Automates typing and sending a WhatsApp message |
| **"Jarvis, search web for latest AI news"** | Opens Chrome & gives you a spoken summary of the top result |
| **"Jarvis, send message — meeting at 5"** | Sends a text message to your configured Telegram chat |
| **"Jarvis, send voice note — I'll be late"** | Records and sends a voice note to you on Telegram |
| **"Jarvis, set reminder 5 minutes — drink water"** | Sets a local timer and reminds you in 5 minutes |
| **"Jarvis, what is Python?"** | Consults its local AI Brain (Ollama) and answers your question |

---

## 🔌 Custom Plugins

Want to add your own features? It's incredibly easy.
Just drop a Python script into `~/.superai/plugins/` that registers a new function. The AI will automatically read your plugin, learn what it does, and start using it the next time you talk to it!

---

## 💻 Requirements

To run Synapse-Assistant-AI smoothly, your system needs:
- **OS:** Windows, macOS, or Linux
- **Python:** Version 3.10 or higher
- **Hardware:**
  - Working Microphone
  - 6 GB RAM (minimum, 8GB+ recommended)
  - ~1.5 GB free disk space (for AI models)
- **Internet:** Only required for the first-time model download and web search commands.
- **Screen Reading (OCR):** To use the "read screen" feature, you must have Tesseract OCR installed on your system (`brew install tesseract` on Mac, or `sudo apt install tesseract-ocr` on Ubuntu).

---

## 🛠️ Troubleshooting

- **Installation Errors (vosk / sounddevice):** If you get a "No matching distribution found" error during `pip install`, it means you are using an experimental or unsupported version of Python (like Python 3.13 or 3.14). Please install a stable release like **Python 3.12** and run `python3.12 -m pip install synapse-assistant-ai`.
- **Command Not Found:** If `synapse-ai` says "command not found", you can always run it directly via Python: `python3 -m super_ai`.

---

## 🧠 How it works under the hood

```text
You speak → STT Engine (Vosk) → AI Brain (Ollama/Llama 3) → Action / Answer → TTS Engine → Speaks back
```

Everything runs locally on your machine. 
- **No cloud servers.** 
- **No recurring API bills.** 
- **No data leaves your computer.**

---

## 📄 License

This project is licensed under the MIT License.
