from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

@dataclass
class BotConfig:
    """Bot configuration settings"""

    # API credentials
    bot_token: str
    groq_api_key: str
    admin_ids: List[int] = field(default_factory=list)

    # Database config
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "telegram_bot"

    # AI settings
    ai_model: str = "llama-3.3-70b-versatile"
    vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    ai_temperature: float = 0.7
    max_history_messages: int = 20

    # Rate limiting
    rate_limit_seconds: int = 1
    max_requests_per_minute: int = 20

    # File paths
    # Adjusted paths since this is now in bot/core/ package
    history_file: Path = Path(__file__).parent.parent.parent / "conversation_history.json"
    log_file: Path = Path(__file__).parent.parent.parent / "bot.log"

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

        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", "3306"))
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "")
        db_name = os.getenv("DB_NAME", "telegram_bot")

        return cls(
            bot_token=bot_token,
            groq_api_key=groq_api_key,
            admin_ids=admin_ids,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_password=db_password,
            db_name=db_name,
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
