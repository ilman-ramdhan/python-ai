"""
Telegram AI Bot with Groq Integration

A production-ready, enterprise-grade AI chatbot for Telegram featuring:
- Groq AI integration (Llama 3.3 70B)
- Rate limiting and spam protection
- Persistent conversation history
- Comprehensive error handling and recovery
- Admin monitoring capabilities
- Async architecture for optimal performance

Author: AI Development Team
License: MIT
"""

from __future__ import annotations

import os
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict
from functools import wraps

from groq import Groq
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class BotConfig:
    """Bot configuration settings"""

    # API credentials
    bot_token: str
    groq_api_key: str
    admin_ids: List[int] = field(default_factory=list)

    # AI settings
    ai_model: str = "llama-3.3-70b-versatile"
    ai_temperature: float = 0.7
    max_history_messages: int = 20

    # Rate limiting
    rate_limit_seconds: int = 3
    max_requests_per_minute: int = 20

    # File paths
    history_file: Path = Path(__file__).parent / "conversation_history.json"
    log_file: Path = Path(__file__).parent / "bot.log"

    @classmethod
    def from_env(cls) -> BotConfig:
        """Create configuration from environment variables"""
        load_dotenv()

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        admin_ids_str = os.getenv("ADMIN_IDS", "")

        admin_ids = [
            int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()
        ]

        return cls(
            bot_token=bot_token,
            groq_api_key=groq_api_key,
            admin_ids=admin_ids,
        )

    def validate(self) -> None:
        """Validate required configuration"""
        errors = []

        if not self.bot_token:
            errors.append("TELEGRAM_BOT_TOKEN is required")

        if not self.groq_api_key:
            errors.append("GROQ_API_KEY is required")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))


# ============================================================================
# MESSAGE TEMPLATES
# ============================================================================


class MessageTemplates:
    """Centralized message templates"""

    START = """🤖 *Telegram AI Bot*

Halo! Saya AI assistant powered by Groq.

*Cara Pakai:*
• *Private Chat:* Langsung chat aja!
• *Group Chat:* Mention saya @{bot_username} atau reply chat saya

*Commands:*
/start - Info bot
/help - Bantuan
/clear - Reset percakapan
/stats - Statistik (admin only)

💡 Powered by Llama 3.3 70B"""

    HELP = """📚 *Bantuan*

*Contoh Tanya:*
• "Jelaskan apa itu AI"
• "Hitung 15% dari 500000"
• "Tips nabung yang efektif"
• "Buatkan cerita pendek"

Bot akan ingat percakapan sebelumnya!

*Commands:*
/start - Info
/help - Bantuan
/clear - Reset chat
/stats - Statistics (admin)"""

    PHOTO_NOT_SUPPORTED = """📷 Terima kasih sudah kirim foto!

🚧 Maaf, fitur analisis gambar **belum tersedia** saat ini.

Untuk saat ini, saya hanya bisa membantu dengan:
✅ Chat text
✅ Menjawab pertanyaan
✅ Analisis & diskusi

Silakan tanya dalam bentuk text ya! 😊"""

    STATS = """📊 *Bot Statistics*

👥 Total Chats: {total_chats}
💬 Total Messages: {total_messages}
✅ Active Chats: {active_chats}
🤖 AI Model: {ai_model}
⏱️ Rate Limit: {rate_limit}s/{max_req}req/min"""

    # Error messages
    RATE_LIMIT_GROQ = "⏳ Groq API sedang sibuk. Tunggu sebentar ya..."
    RATE_LIMIT_USER = "⏱️ Terlalu cepat! Tunggu {seconds} detik lagi."
    RATE_LIMIT_MINUTE = "⏱️ Terlalu banyak request! Max {max_requests}/menit."
    NETWORK_ERROR = "🌐 Network error. Coba lagi ya!"
    TIMEOUT_ERROR = "⏰ Request timeout. Pertanyaan terlalu kompleks?"
    API_KEY_ERROR = "🔑 API key error. Check configuration!"
    GENERAL_ERROR = "❌ Maaf, ada error: {error}"
    ADMIN_ONLY = "❌ Command ini hanya untuk admin."
    HISTORY_CLEARED = "✅ Percakapan telah direset!"


# ============================================================================
# LOGGING SETUP
# ============================================================================


def setup_logging(log_file: Path) -> logging.Logger:
    """Configure logging with file and console handlers"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# ============================================================================
# CORE BOT CLASS
# ============================================================================


class TelegramAIBot:
    """Main bot class encapsulating all functionality"""

    def __init__(self, config: BotConfig):
        self.config = config
        self.logger = setup_logging(config.log_file)
        self.groq_client = Groq(api_key=config.groq_api_key)

        # State management
        self.conversation_history: Dict[int, List[Dict[str, str]]] = {}
        self.user_last_request: Dict[int, float] = defaultdict(float)
        self.user_request_count: Dict[int, List[float]] = defaultdict(list)

        # Load persistent history
        self._load_history()

    # ========================================================================
    # PERSISTENCE
    # ========================================================================

    def _load_history(self) -> None:
        """Load conversation history from disk"""
        try:
            if self.config.history_file.exists():
                with open(self.config.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.conversation_history = {int(k): v for k, v in data.items()}
                self.logger.info(f"Loaded history for {len(self.conversation_history)} chats")
        except Exception as e:
            self.logger.error(f"Error loading history: {e}")

    def _save_history(self) -> None:
        """Save conversation history to disk"""
        try:
            with open(self.config.history_file, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            self.logger.debug("History saved")
        except Exception as e:
            self.logger.error(f"Error saving history: {e}")

    # ========================================================================
    # RATE LIMITING
    # ========================================================================

    def check_rate_limit(self, user_id: int) -> Optional[str]:
        """
        Check if user exceeded rate limits

        Args:
            user_id: Telegram user ID

        Returns:
            Error message if rate limited, None otherwise
        """
        current_time = time.time()

        # Per-request cooldown
        time_since_last = current_time - self.user_last_request[user_id]
        if time_since_last < self.config.rate_limit_seconds:
            wait_time = int(self.config.rate_limit_seconds - time_since_last) + 1
            return MessageTemplates.RATE_LIMIT_USER.format(seconds=wait_time)

        # Requests per minute
        self.user_request_count[user_id] = [
            t for t in self.user_request_count[user_id] if current_time - t < 60
        ]

        if len(self.user_request_count[user_id]) >= self.config.max_requests_per_minute:
            return MessageTemplates.RATE_LIMIT_MINUTE.format(
                max_requests=self.config.max_requests_per_minute
            )

        # Update counters
        self.user_last_request[user_id] = current_time
        self.user_request_count[user_id].append(current_time)

        return None

    # ========================================================================
    # AI INTERACTION
    # ========================================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    def _call_groq_api(self, messages: List[Dict[str, str]]) -> str:
        """
        Call Groq API with retry logic

        Args:
            messages: Conversation messages

        Returns:
            AI response text
        """
        response = self.groq_client.chat.completions.create(
            messages=messages,
            model=self.config.ai_model,
            temperature=self.config.ai_temperature,
        )
        return response.choices[0].message.content

    def ask_ai(self, question: str, chat_id: int, use_history: bool = True) -> str:
        """
        Get AI response for user question

        Args:
            question: User's question
            chat_id: Telegram chat ID
            use_history: Whether to use conversation history

        Returns:
            AI response
        """
        try:
            # Build messages
            if use_history and chat_id in self.conversation_history:
                messages = self.conversation_history[chat_id].copy()
                messages.append({"role": "user", "content": question})
            else:
                messages = [{"role": "user", "content": question}]

            # Get AI response
            ai_reply = self._call_groq_api(messages)

            # Save to history
            if use_history:
                self._save_to_history(chat_id, messages, ai_reply)

            self.logger.info(f"AI response generated for chat {chat_id}")
            return ai_reply

        except Exception as e:
            return self._handle_ai_error(e, chat_id)

    def _save_to_history(self, chat_id: int, messages: List, ai_reply: str) -> None:
        """Save conversation to history"""
        if chat_id not in self.conversation_history:
            self.conversation_history[chat_id] = []

        self.conversation_history[chat_id] = messages
        self.conversation_history[chat_id].append({"role": "assistant", "content": ai_reply})

        # Limit size
        if len(self.conversation_history[chat_id]) > self.config.max_history_messages:
            self.conversation_history[chat_id] = self.conversation_history[chat_id][
                -self.config.max_history_messages :
            ]

        self._save_history()

    def _handle_ai_error(self, error: Exception, chat_id: int) -> str:
        """Handle AI errors gracefully"""
        error_str = str(error).lower()

        if "rate" in error_str or "limit" in error_str:
            self.logger.warning(f"Rate limit for chat {chat_id}")
            return MessageTemplates.RATE_LIMIT_GROQ
        elif "timeout" in error_str:
            self.logger.warning(f"Timeout for chat {chat_id}")
            return MessageTemplates.TIMEOUT_ERROR
        elif "network" in error_str or "connection" in error_str:
            self.logger.error(f"Network error for chat {chat_id}: {error}")
            return MessageTemplates.NETWORK_ERROR
        elif "api" in error_str and "key" in error_str:
            self.logger.error(f"API key error: {error}")
            return MessageTemplates.API_KEY_ERROR
        else:
            self.logger.error(f"Unexpected error for chat {chat_id}: {error}")
            return MessageTemplates.GENERAL_ERROR.format(error=str(error)[:100])

    # ========================================================================
    # UTILITIES
    # ========================================================================

    @staticmethod
    def is_group_chat(chat_type: str) -> bool:
        """Check if chat is a group"""
        return chat_type in ["group", "supergroup"]

    @staticmethod
    async def is_bot_mentioned(message, bot_username: str) -> bool:
        """Check if bot is mentioned in message"""
        text = message.text or message.caption or ""

        # Check mention
        if f"@{bot_username}" in text:
            return True

        # Check reply
        if message.reply_to_message:
            bot = await message.get_bot()
            return message.reply_to_message.from_user.id == bot.id

        return False

    @staticmethod
    def remove_bot_mention(text: str, bot_username: str) -> str:
        """Remove bot mention from text"""
        return text.replace(f"@{bot_username}", "").strip()

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.config.admin_ids

    def clear_history(self, chat_id: int) -> None:
        """Clear conversation history for chat"""
        if chat_id in self.conversation_history:
            self.conversation_history[chat_id] = []
            self._save_history()

    def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics"""
        return {
            "total_chats": len(self.conversation_history),
            "total_messages": sum(len(h) for h in self.conversation_history.values()),
            "active_chats": len([h for h in self.conversation_history.values() if h]),
        }

    # ========================================================================
    # COMMAND HANDLERS
    # ========================================================================

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        bot = await context.bot.get_me()
        message = MessageTemplates.START.format(bot_username=bot.username)
        await update.message.reply_text(message, parse_mode="Markdown")
        self.logger.info(f"/start by user {update.message.from_user.id}")

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        await update.message.reply_text(MessageTemplates.HELP, parse_mode="Markdown")
        self.logger.info(f"/help by user {update.message.from_user.id}")

    async def cmd_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /clear command"""
        self.clear_history(update.message.chat_id)
        await update.message.reply_text(MessageTemplates.HISTORY_CLEARED)
        self.logger.info(f"/clear by user {update.message.from_user.id}")

    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command (admin only)"""
        user_id = update.message.from_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text(MessageTemplates.ADMIN_ONLY)
            self.logger.warning(f"Unauthorized /stats by user {user_id}")
            return

        stats = self.get_stats()
        message = MessageTemplates.STATS.format(
            total_chats=stats["total_chats"],
            total_messages=stats["total_messages"],
            active_chats=stats["active_chats"],
            ai_model=self.config.ai_model,
            rate_limit=self.config.rate_limit_seconds,
            max_req=self.config.max_requests_per_minute,
        )

        await update.message.reply_text(message, parse_mode="Markdown")
        self.logger.info(f"/stats by admin {user_id}")

    # ========================================================================
    # MESSAGE HANDLERS
    # ========================================================================

    async def handle_text_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle text messages"""
        message = update.message
        user_id = message.from_user.id
        chat_id = message.chat_id
        user_message = message.text

        # Rate limit check
        rate_limit_error = self.check_rate_limit(user_id)
        if rate_limit_error:
            await message.reply_text(rate_limit_error)
            self.logger.warning(f"Rate limit: user {user_id}")
            return

        # Group mention check
        bot = await context.bot.get_me()
        is_group = self.is_group_chat(message.chat.type)

        if is_group:
            if not await self.is_bot_mentioned(message, bot.username):
                return
            user_message = self.remove_bot_mention(user_message, bot.username)

        # Log
        chat_name = message.chat.title if is_group else "Private"
        self.logger.info(f"[{chat_name}] {message.from_user.first_name}: {user_message[:50]}")

        # Show typing
        typing_task = asyncio.create_task(self._send_typing_action(message.chat))

        try:
            # Get AI response
            response = self.ask_ai(user_message, chat_id)
            typing_task.cancel()

            # Send
            await message.reply_text(response)
            self.logger.info(f"Response sent: {response[:50]}")

        except Exception as e:
            typing_task.cancel()
            self.logger.error(f"Error: {e}")
            await message.reply_text(MessageTemplates.GENERAL_ERROR.format(error=str(e)[:100]))

    async def handle_photo_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle photo messages"""
        message = update.message
        user_id = message.from_user.id

        # Rate limit
        rate_limit_error = self.check_rate_limit(user_id)
        if rate_limit_error:
            await message.reply_text(rate_limit_error)
            return

        # Group mention check
        bot = await context.bot.get_me()
        is_group = self.is_group_chat(message.chat.type)

        if is_group and not await self.is_bot_mentioned(message, bot.username):
            return

        # Log
        chat_name = message.chat.title if is_group else "Private"
        self.logger.info(f"[{chat_name}] Photo - Not supported")

        await message.reply_text(MessageTemplates.PHOTO_NOT_SUPPORTED)

    async def _send_typing_action(self, chat, duration: int = 10) -> None:
        """Send typing action indicator"""
        try:
            for _ in range(duration):
                await chat.send_action(action="typing")
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    # ========================================================================
    # BOT LIFECYCLE
    # ========================================================================

    def build_application(self) -> Application:
        """Build and configure bot application"""
        app = Application.builder().token(self.config.bot_token).build()

        # Commands
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(CommandHandler("clear", self.cmd_clear))
        app.add_handler(CommandHandler("stats", self.cmd_stats))

        # Messages
        app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo_message))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message)
        )

        return app

    def run(self) -> None:
        """Start the bot"""
        self.logger.info("Bot starting...")

        # Print startup info
        print("\n" + "=" * 60)
        print("🤖 TELEGRAM AI BOT - PRODUCTION MODE")
        print("=" * 60)
        print(f"🧠 AI Model: {self.config.ai_model}")
        print(f"📱 Bot Token: {self.config.bot_token[:20]}...")
        print(f"⏱️  Rate Limit: {self.config.rate_limit_seconds}s / {self.config.max_requests_per_minute} req/min")
        print(f"💾 History: {len(self.conversation_history)} chats")
        print(f"👨‍💼 Admin IDs: {', '.join(map(str, self.config.admin_ids)) or 'None'}")
        print("\n✅ Bot is running! Press Ctrl+C to stop.\n")
        print("=" * 60 + "\n")

        # Build and run
        app = self.build_application()
        self.logger.info("Bot started successfully")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Main entry point"""
    try:
        # Load and validate config
        config = BotConfig.from_env()
        config.validate()

        # Create and run bot
        bot = TelegramAIBot(config)
        bot.run()

    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped! Bye!")
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        logging.exception("Fatal error occurred")


if __name__ == "__main__":
    main()
