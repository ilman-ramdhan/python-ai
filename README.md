# 🤖 Telegram AI Bot

Enterprise-grade Telegram bot dengan Groq AI integration, built dengan Python best practices.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/AI-Groq-orange.svg)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ Features

### Core Features
- 🤖 **AI Chat** - Powered by Groq Llama 3.3 70B
- �️ **Vision / Photo Analysis** - Can see and analyze images (Llama Vision)
- �💬 **Conversation History** - Persistent chat memory
- 👥 **Group Support** - Mention-only responses (no spam)
- ⌨️ **Typing Indicator** - Natural chat experience
- ⚡ **Fast & Free** - Groq API integration

### Production Features
- 📝 **Logging System** - File & console logging
- ⏱️ **Rate Limiting** - Anti-spam protection (3s cooldown + 20 req/min)
- 💾 **Persistent Storage** - JSON-based history (survives restarts)
- ✅ **Config Validation** - Environment variable checking
- 🔄 **Error Recovery** - Auto-retry with exponential backoff
- 👨‍💼 **Admin Commands** - Statistics & monitoring
- 💬 **User-Friendly Errors** - Specific error messages
- 🏗️ **OOP Architecture** - Clean, maintainable code

---

## � Prerequisites

Before running the bot, you need to set up the necessary accounts and keys.

### 1. Create a Telegram Bot
1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**.
2. Send the command `/newbot`.
3. Follow the instructions to name your bot (e.g., "My AI Assistant") and give it a username (must end in `_bot`).
4. **Copy the API Token** provided by BotFather. You will need this for the `TELEGRAM_BOT_TOKEN`.

### 2. Get Groq API Key
1. Sign up or Login at [Groq Console](https://console.groq.com/).
2. Go to the API Keys section and create a new key.
3. Copy the key. You will need this for the `GROQ_API_KEY`.

### 3. Get Your Telegram ID (Optional)
To use admin commands like `/stats`:
1. Search for **[@userinfobot](https://t.me/userinfobot)** in Telegram.
2. Start the bot to see your numeric User ID.

---

## �🚀 Quick Start

### 1. Install Dependencies
```bash
pip install groq python-telegram-bot python-dotenv tenacity
```

### 2. Configuration
Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=your_telegram_user_id  # Optional
```



### 3. Run Bot
```bash
python main.py
```

Bot is now running! 🎉

---

## 💬 Usage

### Private Chat
1. Open bot in Telegram
2. Send message: `"Hello!"`
3. Bot responds instantly

### Group Chat
1. Add bot to your group
2. Mention bot: `@botname what is AI?`
3. Or reply to bot's message
4. Bot only responds when mentioned (no spam!)

### Commands
- `/start` - Bot information
- `/help` - Usage guide
- `/clear` - Reset conversation history
- `/stats` - Bot statistics (admin only)

---

## 🏗️ Architecture

### Code Structure
```
main.py                          # Entry point
└── bot/                         # Source code package
    ├── config.py                # BotConfig & validation
    ├── handlers.py              # Command & Message processors
    ├── ai.py                    # Groq AI integration
    ├── persistence.py           # JSON history management
    ├── templates.py             # Message string templates
    └── logger.py                # Logging configuration
```

### Key Features
- **Type Hints** - Full typing for IDE support
- **Error Handling** - Comprehensive try-catch with specific messages
- **Async/Await** - Non-blocking architecture
- **Retry Logic** - Tenacity-based error recovery
- **PEP 8 Compliant** - Clean, readable code

---

## 📁 Project Files

```
python-ai/
├── main.py                      # Main entry point
├── bot/                         # Source code package
├── passenger_wsgi.py            # cPanel / Passenger entry point
├── .env                         # Configuration (DO NOT COMMIT!)
├── .env.example                 # Configuration template
├── .gitignore                   # Git exclusions
├── bot.log                      # Runtime logs (auto-generated)
├── conversation_history.json    # Chat history (auto-generated)
└── README.md                    # This file
```

---

## 🎯 Use Cases

- 💻 **Coding Help** - Debugging, code review, explanations
- 📝 **Writing** - Content creation, translation, proofreading
- 🧮 **Calculations** - Math, finance, data analysis
- 🎓 **Learning** - Explain concepts, tutorials, Q&A
- 💡 **Brainstorming** - Ideas, planning, problem-solving
- 🗣️ **General Chat** - Conversations, advice, entertainment

---

## 🔧 Configuration Options

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ | Groq API key for AI |
| `TELEGRAM_BOT_TOKEN` | ✅ | Telegram bot token |
| `ADMIN_IDS` | ❌ | Comma-separated admin user IDs |

### Bot Settings (in code)
- **AI Model**: `llama-3.3-70b-versatile`
- **Vision Model**: `llama-4-scout-17b-16e-instruct`
- **Temperature**: `0.7`
- **Max History**: `20 messages`
- **Rate Limit**: `3 seconds` between requests
- **Max Requests**: `20` per minute per user

---

## 📊 Technical Details

### Technologies
- **Python** 3.9+
- **python-telegram-bot** - Telegram API wrapper
- **Groq** - AI API client
- **Tenacity** - Retry logic
- **Asyncio** - Async architecture

### Error Handling
- Network errors → Auto-retry with backoff
- Rate limits → User-friendly wait messages
- API errors → Specific error descriptions
- Timeouts → Graceful fallback

### Rate Limiting
- **Per-request**: 3 second cooldown
- **Per-minute**: Max 20 requests
- **Prevents**: Spam & API abuse

### Data Persistence
- **Format**: JSON
- **Location**: `conversation_history.json`
- **Auto-save**: After each message
- **Max size**: 20 messages per chat

---

## 🧪 Development

### Best Practices Applied
- ✅ Object-Oriented Design
- ✅ Dataclass Configuration
- ✅ Comprehensive Type Hints
- ✅ Centralized Message Templates
- ✅ Separation of Concerns
- ✅ Private/Public Method Distinction
- ✅ Comprehensive Docstrings
- ✅ PEP 8 Compliance

### Testing Ready
```python
# Easy to test
config = BotConfig(bot_token="test", groq_api_key="test")
bot = TelegramAIBot(config)

# Mock dependencies
bot.groq_client = MockGroqClient()
response = bot.ask_ai("test", 123)
```

---

## 📝 Logging

Logs are written to:
- **File**: `bot.log`
- **Console**: Real-time output

Log entries include:
- Timestamps
- User interactions
- AI responses
- Errors & warnings
- Admin actions

---

## 🔒 Security

- ✅ Environment variables (no hardcoded keys)
- ✅ `.gitignore` configured
- ✅ Rate limiting protection
- ✅ Admin-only commands
- ✅ Input validation

**Important**: Never commit `.env` file!

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Follow PEP 8 guidelines
4. Add type hints
5. Update documentation
6. Submit pull request

---

## 📄 License

MIT License - feel free to use and modify!

---

## 🙏 Credits

- **AI**: [Groq](https://groq.com/) (Llama 3.3 70B)
- **Framework**: [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- **Built with**: Python & Love ❤️

---

## 📞 Support

Having issues? Check:
1. `bot.log` - Error logs
2. `bot.log` - Error logs
3. Environment variables - Correct configuration



## ❓ Troubleshooting

### Bot not responding
- Check if `TELEGRAM_BOT_TOKEN` is correct.
- Check if the bot process is running (`python main.py`).
- Check `bot.log` for errors.

### "Rate limit exceeded"
- You are sending messages too fast. Wait 3 seconds.

### Vision not working (Analyzing image...)
- Ensure your `GROQ_API_KEY` is valid.
- Check if the model name in `config.py` is supported by Groq.

---

**Made with 🤖 by [Ilman M Ramdhan](https://github.com/ilmanramdhan)** | Powered by Groq & Telegram
