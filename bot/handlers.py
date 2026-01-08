import logging
import asyncio
import time
import base64
from io import BytesIO
from collections import defaultdict
from typing import Dict, List, Any

from telegram import Update
from telegram.ext import ContextTypes

from .core.config import BotConfig
from .resources.templates import MessageTemplates
from .services.ai_service import AIService
from .services.storage_service import StorageService
from .services.excel_service import ExcelService
import json
import re

logger = logging.getLogger("bot.handlers")

class TelegramBot:
    """Class enabling the handling of bot commands and messages"""

    def __init__(
        self,
        config: BotConfig,
        ai_service: AIService,
        storage: StorageService,
    ):
        self.config = config
        self.ai = ai_service
        self.storage = storage
        
        # Rate limiting
        self.user_last_request: Dict[int, float] = defaultdict(float)
        self.user_request_count: Dict[int, List[float]] = defaultdict(list)
        
    async def initialize(self):
        """Async initialization"""
        # self.conversation_history is removed in favor of fetching on demand from DB
        # self.conversation_history = await self.storage.load_history() # No longer loading all history into memory

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
        # Save individually
        await self.storage.save_message(chat_id, "user", user_msg)
        await self.storage.save_message(chat_id, "assistant", ai_msg)

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
        # Stats are harder with direct DB access without counting queries. 
        # For now, return placeholders or implement count queries in persistence.
        return {
            "total_chats": "N/A (DB)",
            "total_messages": "N/A (DB)", 
            "active_chats": "N/A (DB)",
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
        await self.storage.clear_history(chat_id)
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



    async def _get_excel_data_from_ai(self, prompt: str, image_base64: str = None) -> Dict[str, Any]:
        """Get structured Excel data from AI (Text or Vision)"""
        
        system_instruction = (
            "You are a data extraction assistant. "
            "Generate a valid JSON object representing an Excel file based on the user request. "
            "The JSON MUST follow this exact schema:\n"
            "{\n"
            "  \"filename\": \"string (ending in .xlsx)\",\n"
            "  \"sheets\": [\n"
            "    {\n"
            "      \"name\": \"string (sheet name)\",\n"
            "      \"headers\": [\"string\", \"string\"],\n"
            "      \"rows\": [[\"value\", \"value\"], [\"value\", \"value\"]]\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "IMPORTANT: Return ONLY the raw JSON string. Do not use markdown code blocks (```json). "
            "Do not add any explanation."
        )

        messages = []
        model = self.config.ai_model

        if image_base64:
            # Vision Request
            model = self.config.vision_model
            messages = [
                {
                    "role": "system", 
                    "content": system_instruction
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                            },
                        },
                    ],
                }
            ]
        else:
            # Text Request
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]

        # Call AI
        json_response = await self.ai.get_response(messages, model=model)
        
        # Robust JSON Extraction
        try:
            # 1. Try to find code block
            match = re.search(r'```json\s*(.*?)\s*```', json_response, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                # 2. Try to find substring starting with { and ending with }
                # This helps if the model returns text before/after without markdown blocks
                json_match = re.search(r'(\{.*\})', json_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # 3. Fallback: try raw string, might be pure JSON
                    json_str = json_response

            return json.loads(json_str)

        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from AI: {json_response}")
            raise

    async def cmd_excel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /excel command to generate Excel files from Text OR Images"""
        user_id = update.message.from_user.id
        message = update.message
        
        # 1. Determine Input Source (Text vs Image)
        prompt = ""
        image_file = None
        
        # Check args for prompt
        if context.args:
            prompt = " ".join(context.args)
        
        # Check for image in current message (Caption command)
        if message.photo:
            image_file = await context.bot.get_file(message.photo[-1].file_id)
            if not prompt:
                prompt = message.caption or "Extract data from this image to Excel"
        
        # Check for reply to image
        elif message.reply_to_message and message.reply_to_message.photo:
            image_file = await context.bot.get_file(message.reply_to_message.photo[-1].file_id)
            if not prompt:
                prompt = "Extract data from this image to Excel"
                if message.text:
                     prompt += f". Context: {message.text}"

        # Fallback for Reply to Text
        elif message.reply_to_message and message.reply_to_message.text:
             if not prompt:
                 prompt = message.reply_to_message.text
        
        # Validation
        if not prompt and not image_file:
            await update.message.reply_text(
                "⚠️ Please provide a description, upload a photo with caption, or reply to a message.\n"
                "Example: `/excel List of top 10 programming languages`",
                parse_mode="Markdown"
            )
            return

        # Rate limit
        if error := self.check_rate_limit(user_id):
            await update.message.reply_text(error)
            return

        status_msg = await update.message.reply_text("📊 Analyzing request & generating Excel...")
        logger.info(f"/excel by user {user_id}. Has Image: {bool(image_file)}")

        try:
            # 2. Process Image if exists
            image_base64 = None
            if image_file:
                image_base64 = await self._download_and_encode_image(image_file)

            # 3. Get Structured Data
            data = await self._get_excel_data_from_ai(prompt, image_base64)

            # 4. Generate Excel
            excel_file, filename = ExcelService.generate(data)

            # 5. Send File
            await update.message.reply_document(
                document=excel_file,
                filename=filename,
                caption=f"✅ Excel generated from {'📷 Image' if image_file else '📝 Text'}"
            )
            
            # Cleanup status message (optional, usually better to leave or delete)
            # await status_msg.delete() 

        except json.JSONDecodeError:
            await update.message.reply_text("❌ AI output invalid JSON. Please try again with a clearer prompt.")
        except Exception as e:
            logger.error(f"Error generating excel: {e}", exc_info=True)
            await update.message.reply_text(MessageTemplates.GENERAL_ERROR.format(error="Failed to generate Excel file."))

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
            # Prepare messages (fetch context from DB)
            recent_context = await self.storage.get_chat_history(chat_id, limit=self.config.max_history_messages)
            messages = recent_context + [{"role": "user", "content": user_message}]
            
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

        # Ignore if this is a command (handled by CommandHandler) or delegate if needed
        # Fix: Check this BEFORE rate limit to avoid double counting if we delegate to cmd_excel
        if caption and caption.startswith("/excel"):
             await self.cmd_excel(update, context)
             return

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
        # Only analyze if validation passes (e.g. not a command)
        # Commands in captions are handled by CommandHandler, but we should ensure we don't double process if needed.
        # However, CommandHandler usually stops propagation.
        
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
