"""
Telegram AI Bot with Groq Integration

Author: Ilman M Ramdhan
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

from bot.core.config import BotConfig
from bot.core.logger import setup_logging
from bot.services.storage_service import StorageService
from bot.services.ai_service import AIService
from bot.handlers import TelegramBot

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
        storage = StorageService(config)
        ai_service = AIService(config)
        
        # 4. Initialize Handlers
        bot_app = TelegramBot(config, ai_service, storage)

        # 6. Register Handlers
        async def post_init(application: Application) -> None:
            await storage.initialize()
            # await bot_app.initialize() # No longer needed for handlers to load history
            logger.info("Services & Handlers initialized")

        # 5. Build Application
        app = Application.builder().token(config.bot_token).post_init(post_init).build()

        # Commands
        app.add_handler(CommandHandler("start", bot_app.cmd_start))
        app.add_handler(CommandHandler("help", bot_app.cmd_help))
        app.add_handler(CommandHandler("clear", bot_app.cmd_clear))
        app.add_handler(CommandHandler("stats", bot_app.cmd_stats))
        app.add_handler(CommandHandler("excel", bot_app.cmd_excel))

        # Messages
        app.add_handler(MessageHandler(filters.PHOTO, bot_app.handle_photo_message))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, bot_app.handle_text_message)
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
