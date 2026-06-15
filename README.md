# 🤖 Synapse-Assistant-AI — Free Offline Voice-Controlled Assistant

**Install. Run. Talk.** That's it. 

Synapse-Assistant-AI is a completely offline, privacy-first, voice-controlled AI assistant for your computer. It listens to your voice commands, processes them locally without sending your data to any cloud, performs desktop automation tasks, and speaks back to you.

---

## 🌟 Key Features

- **100% Offline & Private:** Uses local LLMs (via Ollama) and offline Speech-to-Text (Vosk). No API keys, no internet required (except for initial setup and web searches).
- **Voice-Controlled:** Always listening for its wake word (e.g., "Jarvis", "Friday", or your custom name).
- **Conversational Chat (v0.2.6):** It's not just a strict bot! You can talk to it freely (e.g., "Write a song for me", "Tell me a joke", "Solve this math problem") and it replies naturally using its LLM brain.
- **Smart Clarifications (v0.2.6):** If you ask it to perform a task but forget to give details (like "Send a WhatsApp message" without a phone number), it will politely ask you for the missing information before executing.
- **Smarter Brain & Robust Parsing (v0.2.7):** Upgraded the core LLM from 1B to the drastically smarter **Llama 3.2 3B** parameter model for flawless instruction following and Hindi/Hinglish comprehension. Added a robust fallback JSON parser so desktop automation never crashes.
- **Context Memory:** Remembers your recent conversation history so you can ask follow-up questions naturally.
- **Vision & Clipboard:** Can read your screen (OCR) and read your copied clipboard text.
- **Plugin System:** Easily extend the AI's capabilities by dropping Python scripts into a plugins folder.
- **Desktop Automation:** Open websites, launch apps, play media, and search the web hands-free.
- **Smart Notifications:** Automatically notifies you via a Telegram Bot when a background task completes.
- **WhatsApp Integration:** Automates sending WhatsApp messages to your contacts.

---

## 🚀 Installation

Ensure you have Python 3.10 or higher installed.

**For Windows:**
```cmd
pip install synapse-assistant-ai
```

**For macOS / Linux:**
```bash
pip3 install synapse-assistant-ai
```

*(Note: On macOS and Linux, you might need to use `pip3` instead of `pip` depending on your setup).*

> **⚠️ Linux Users:** If you get an `externally-managed-environment` error during install, run:
> `pip3 install synapse-assistant-ai --break-system-packages` or use `pipx install synapse-assistant-ai`.

---

## ⚙️ Quick Start & Setup

Run the assistant from your terminal:

```bash
synapse-ai
```

```bash
synapse-ai
```

> **🛑 "command not found" on Linux?**
> When you install via `pip` on Linux without a virtual environment, Python places the command in your local bin folder (`~/.local/bin`), which might not be in your system's PATH. 
> 
> **How to fix:**
> 1. Run it directly using its full path: `~/.local/bin/synapse-ai`
> 2. **OR** add it to your PATH permanently so the `synapse-ai` command works everywhere:
>    ```bash
>    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
>    source ~/.bashrc
>    ```

**First-Time Interactive Setup:**
The first time you run the command, an interactive setup will start right in your terminal:
1. **Name your AI:** Choose a wake word (e.g., Jarvis, Friday, or Hey AI).
2. **Telegram Notifications (Optional):** If you want to receive task completion alerts on your phone, you will be prompted to paste your Telegram Bot Token and Chat ID directly in the terminal. **No `.env` editing required!**
3. **Model Download:** It will auto-download the necessary AI voice models (~2.1 GB, one-time only).

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
| **"Jarvis, what is the time?"** | Instantly tells you the current local time |
| **"Jarvis, can you write a short poem?"** | Replies naturally with a generated poem using its LLM brain |
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
- **Command Not Found Error:** If your terminal says `command not found: synapse-ai`, it means your system's PATH is not configured for Python CLI tools. We have built an automated setup to fix this!

  **For Windows Users:**
  1. Open your Command Prompt or PowerShell.
  2. Run the auto-setup command: `python -m super_ai setup`
  3. Close and reopen your Command Prompt. You can now use the `synapse-ai` command forever!

  **For macOS / Linux Users:**
  1. Open your Terminal.
  2. Run the auto-setup command: `python3 -m super_ai setup`
  3. Restart your terminal or run `source ~/.zshrc` (or `source ~/.bashrc` on Linux). You can now use the `synapse-ai` command flawlessly!

  *(Fallback: If you still face issues, you can always run the assistant directly from anywhere by typing `python3 -m super_ai` or `python -m super_ai`)*

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
