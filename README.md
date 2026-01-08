# 🤖 Telegram AI Bot

Enterprise-grade Telegram bot powered by **Groq AI (Llama 3)**, featuring **Excel Generation**, **Vision Analysis**, and a scalable **Microservices Architecture**.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/AI-Groq-orange.svg)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ Key Features

### 🧠 Advanced AI
- **Chat**: Powered by `llama-3.3-70b` for natural, intelligent conversations.
- **Vision**: Uses `llama-3.2-11b-vision` to analyze photos (e.g., "What's in this image?").
- **Context Aware**: Remembers conversation history (configurable depth).

### 📊 Excel Generation (New!)
- **Text to Excel**: `/excel Make a list of top 5 laptops with prices` -> Generates `.xlsx`.
- **Image to Excel**: Upload a photo of a table -> `/excel` -> Extracts data to `.xlsx`.
- **Auto-Formatting**: Auto-adjusts column widths and bold headers.

### 🛡️ Production Ready
- **Rate Limiting**: Protects against spam (Token bucket algorithm).
- **Persistence**: Auto-saves chat history to JSON.
- **Microservices Architecture**: Cleanly separated services for AI, Storage, and Utilities.
- **Async/Await**: Non-blocking I/O for high performance.

---

## 🛠️ Installation

### 1. Requirements
- Python 3.9+
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- Groq API Key ([console.groq.com](https://console.groq.com))

### 2. Setup
```bash
# Clone repository
git clone https://github.com/ilmanramdhan/python-ai.git
cd python-ai

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
ADMIN_IDS=123456789,987654321
```

### 4. Run
```bash
python main.py
```

---

## 📖 Usage Guide

### 💬 Chat
Just send a message!
> **User**: "Jelaskan tentang Python dalam 1 kalimat"
> **Bot**: "Python adalah bahasa pemrograman serbaguna yang mudah dibaca dan populer untuk pengembangan web, data science, dan AI."

### 📊 Excel Generation
**Method 1: From Text**
> `/excel Buatkan tabel jadwal belajar mingguan untuk programmer`

**Method 2: From Image (OCR/Vision)**
1. Upload a photo of a document/table.
2. Caption it with `/excel` (or reply to it with `/excel`).
3. Bot will analyze the image and send back an `.xlsx` file.

### 📷 Vision Analysis
Send any photo.
> **User**: [Sends Photo] "Where is this?"
> **Bot**: "Based on the landmarks, this appears to be..."

### 🛠️ Commands
- `/start` - Check bot status.
- `/clear` - clear conversation memory.
- `/stats` - View bot statistics (Admin only).
- `/excel` - Generate Excel files.

---

## 🏗️ Project Structure

Refactored to follow **Clean Architecture** principles:

```text
python-ai/
├── main.py                  # Entry point
├── bot/
│   ├── core/                # Core infrastructure
│   │   ├── config.py        # Settings & Validation
│   │   └── logger.py        # Centralized logging
│   │
│   ├── services/            # Business Logic Layer
│   │   ├── ai_service.py    # Groq API wrapper
│   │   ├── excel_service.py # OpenPYXL generation logic
│   │   └── storage_service.py # Persistence manager
│   │
│   ├── resources/           # Static Assets
│   │   └── templates.py     # Message strings
│   │
│   └── handlers.py          # Telegram Event Controllers
│
├── tests/                   # Verification Scripts
└── conversation_history.json # Data storage
```

---

## 🤝 Contributing
1. Fork the repo.
2. Create feature branch: `git checkout -b feature/cool-feature`.
3. Commit changes: `git commit -m 'Add cool feature'`.
4. Push to branch: `git push origin feature/cool-feature`.
5. Submit a Pull Request.

---

## 📄 License
MIT License. Created by [Ilman M Ramdhan](https://github.com/ilmanramdhan).
