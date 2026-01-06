import logging
import asyncio
import time
import base64
from io import BytesIO
from collections import defaultdict
from typing import Dict, List, Any

from telegram import Update
from telegram.ext import ContextTypes

from .config import BotConfig
from .templates import MessageTemplates
from .ai import AIService
from .persistence import PersistenceManager

logger = logging.getLogger("bot.handlers")

class BotHandlers:
    """Class enabling the handling of bot commands and messages"""

    def __init__(
        self,
        config: BotConfig,
        ai_service: AIService,
        persistence: PersistenceManager,
    ):
        self.config = config
        self.ai = ai_service
        self.persistence = persistence
        self.conversation_history: Dict[int, List[Dict[str, Any]]] = {}
        
        # Rate limiting state
        self.user_last_request: Dict[int, float] = defaultdict(float)
        self.user_request_count: Dict[int, List[float]] = defaultdict(list)

    async def initialize(self):
        """Async initialization"""
        self.conversation_history = await self.persistence.load_history()

    # ========================================================================
    # RATE LIMITING
    # ========================================================================

    def check_rate_limit(self, user_id: int) -> str | None:
        """Check if user exceeded rate limits"""
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
    # HISTORY MANAGEMENT
    # ========================================================================

    async def _update_history(self, chat_id: int, user_msg: str, ai_msg: str):
        """Update and save conversation history"""
        if chat_id not in self.conversation_history:
            self.conversation_history[chat_id] = []

        history = self.conversation_history[chat_id]
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": ai_msg})

        # Trim history
        if len(history) > self.config.max_history_messages:
            self.conversation_history[chat_id] = history[-self.config.max_history_messages:]

        await self.persistence.save_history(self.conversation_history)

    # ========================================================================
    # UTILITIES
    # ========================================================================

    @staticmethod
    def is_group_chat(chat_type: str) -> bool:
        return chat_type in ["group", "supergroup"]

    @staticmethod
    async def is_bot_mentioned(message, bot_username: str) -> bool:
        text = message.text or message.caption or ""
        if f"@{bot_username}" in text:
            return True
        if message.reply_to_message:
            bot = await message.get_bot()
            return message.reply_to_message.from_user.id == bot.id
        return False

    @staticmethod
    def remove_bot_mention(text: str, bot_username: str) -> str:
        return text.replace(f"@{bot_username}", "").strip()

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.config.admin_ids

    def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics"""
        return {
            "total_chats": len(self.conversation_history),
            "total_messages": sum(len(h) for h in self.conversation_history.values()),
            "active_chats": len([h for h in self.conversation_history.values() if h]),
        }
    
    async def _download_and_encode_image(self, photo_file) -> str:
        """Download image and convert to base64"""
        byte_stream = BytesIO()
        await photo_file.download_to_memory(byte_stream)
        byte_stream.seek(0)
        return base64.b64encode(byte_stream.read()).decode('utf-8')

    # ========================================================================
    # COMMAND HANDLERS
    # ========================================================================

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        bot = await context.bot.get_me()
        message = MessageTemplates.START.format(bot_username=bot.username)
        await update.message.reply_text(message, parse_mode="Markdown")
        logger.info(f"/start by user {update.message.from_user.id}")

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(MessageTemplates.HELP, parse_mode="Markdown")
        logger.info(f"/help by user {update.message.from_user.id}")

    async def cmd_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.message.chat_id
        if chat_id in self.conversation_history:
            self.conversation_history[chat_id] = []
            await self.persistence.save_history(self.conversation_history)
        await update.message.reply_text(MessageTemplates.HISTORY_CLEARED)
        logger.info(f"/clear by user {update.message.from_user.id}")

    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.message.from_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text(MessageTemplates.ADMIN_ONLY)
            logger.warning(f"Unauthorized /stats by user {user_id}")
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
        logger.info(f"/stats by admin {user_id}")

    # ========================================================================
    # MESSAGE HANDLERS
    # ========================================================================

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user_id = message.from_user.id
        chat_id = message.chat_id
        user_message = message.text

        # Rate limit check
        if error := self.check_rate_limit(user_id):
            await message.reply_text(error)
            logger.warning(f"Rate limit: user {user_id}")
            return

        # Group processing
        bot = await context.bot.get_me()
        is_group = self.is_group_chat(message.chat.type)
        if is_group:
            if not await self.is_bot_mentioned(message, bot.username):
                return
            user_message = self.remove_bot_mention(user_message, bot.username)

        logger.info(f"[{'Group' if is_group else 'Private'}] {message.from_user.first_name}: {user_message[:50]}")
        
        # Typing indicator
        async def send_typing():
            try:
                while True:
                    await message.chat.send_action(action="typing")
                    await asyncio.sleep(4)
            except asyncio.CancelledError:
                pass
                
        typing_task = asyncio.create_task(send_typing())

        try:
            # Prepare messages
            current_history = self.conversation_history.get(chat_id, []).copy()
            messages = current_history + [{"role": "user", "content": user_message}]
            
            # Get AI Response
            ai_reply = await self.ai.get_response(messages)
            
            typing_task.cancel()
            await message.reply_text(ai_reply)
            
            # Update history
            await self._update_history(chat_id, user_message, ai_reply)
            logger.info(f"Response sent to {chat_id}")

        except Exception as e:
            typing_task.cancel()
            logger.error(f"Error handling message: {e}", exc_info=True)
            
            error_msg = MessageTemplates.GENERAL_ERROR.format(error=str(e)[:100])
            await message.reply_text(error_msg)

    async def handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.message
        user_id = message.from_user.id
        chat_id = message.chat_id
        caption = message.caption or "What can you see in this image?"

        # Rate limit check
        if error := self.check_rate_limit(user_id):
            await message.reply_text(error)
            return

        # Group processing
        bot = await context.bot.get_me()
        is_group = self.is_group_chat(message.chat.type)
        if is_group:
            if not await self.is_bot_mentioned(message, bot.username):
                return
            caption = self.remove_bot_mention(caption, bot.username)

        logger.info(f"[{'Group' if is_group else 'Private'}] Photo from {message.from_user.first_name}")
        await message.reply_text("📷 Analyzing image...")

        try:
            # Get highest resolution photo
            photo = message.photo[-1]
            photo_file = await context.bot.get_file(photo.file_id)
            
            # Encode image
            base64_image = await self._download_and_encode_image(photo_file)
            
            # Prepare payload for Vision Model
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": caption},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ]
            
            # Call AI with Vision Model
            response = await self.ai.get_response(messages, model=self.config.vision_model)
            
            await message.reply_text(response)
            logger.info("Vision response sent")

        except Exception as e:
            logger.error(f"Error handling photo: {e}", exc_info=True)
            await message.reply_text(MessageTemplates.GENERAL_ERROR.format(error="Failed to analyze image."))
