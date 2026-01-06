"""
Telegram AI Bot with Groq Integration

Author: AI Development Team
License: MIT
"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.config import BotConfig
from bot.logger import setup_logging
from bot.persistence import PersistenceManager
from bot.ai import AIService
from bot.handlers import BotHandlers

def main() -> None:
    """Main entry point"""
    try:
        # 1. Load Config
        config = BotConfig.from_env()
        config.validate()

        # 2. Setup Logging
        logger = setup_logging(config.log_file)
        logger.info("Bot starting...")

        # 3. Initialize Services
        persistence = PersistenceManager(config.history_file)
        ai_service = AIService(config)
        
        # 4. Initialize Handlers
        handlers = BotHandlers(config, ai_service, persistence)

        # 6. Register Handlers
        async def post_init(application: Application) -> None:
            await handlers.initialize()
            logger.info("Handlers initialized")

        # 5. Build Application
        app = Application.builder().token(config.bot_token).post_init(post_init).build()

        # Commands
        app.add_handler(CommandHandler("start", handlers.cmd_start))
        app.add_handler(CommandHandler("help", handlers.cmd_help))
        app.add_handler(CommandHandler("clear", handlers.cmd_clear))
        app.add_handler(CommandHandler("stats", handlers.cmd_stats))

        # Messages
        app.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo_message))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text_message)
        )

        # Print startup info
        print("\n" + "=" * 60)
        print("🤖 TELEGRAM AI BOT - PRODUCTION MODE (Refactored)")
        print("=" * 60)
        print(f"🧠 AI Model: {config.ai_model}")
        print(f"📱 Bot Token: {config.bot_token[:20]}...")
        print(f"Async Architecture Active")
        print("\n✅ Bot is running! Press Ctrl+C to stop.\n")

        # 7. Run
        app.run_polling(allowed_updates=Update.ALL_TYPES)

    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped! Bye!")
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        logging.exception("Fatal error occurred")

if __name__ == "__main__":
    main()
