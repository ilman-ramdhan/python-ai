import logging
import asyncio
import aiomysql
from typing import Dict, List, Any
from ..core.config import BotConfig

logger = logging.getLogger("bot.services.storage")

class StorageService:
    """Async MySQL persistence storage service for conversation history"""

    def __init__(self, config: BotConfig):
        self.config = config
        self.pool = None

    async def initialize(self):
        """Initialize connection pool and create table"""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                user=self.config.db_user,
                password=self.config.db_password,
                db=self.config.db_name,
                autocommit=True
            )
            
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        CREATE TABLE IF NOT EXISTS chat_history (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            chat_id BIGINT NOT NULL,
                            role VARCHAR(20) NOT NULL,
                            content TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            INDEX idx_chat_id (chat_id)
                        )
                    """)
            logger.info(f"Connected to MySQL database: {self.config.db_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MySQL: {e}")
            raise e

    async def load_history(self) -> Dict[int, List[Dict[str, str]]]:
        """Load recent history for all active chats (optimized for init)
           Note: To avoid loading massive DB into RAM, we might change strategy later.
           For now, we fetch last N messages for simplicity to match old API.
        """
        # In a real DB scenario, we usually don't preload EVERYTHING.
        # But to keep API compatible with handlers.py:
        history = {}
        # This is a simplification. Ideally handlers should fetch on demand.
        return history 

    async def get_chat_history(self, chat_id: int, limit: int = 20) -> List[Dict[str, str]]:
        """Fetch history for a specific chat"""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute("""
                        SELECT role, content 
                        FROM chat_history 
                        WHERE chat_id = %s 
                        ORDER BY id DESC 
                        LIMIT %s
                    """, (chat_id, limit))
                    result = await cur.fetchall()
                    # Reverse to chronological order (oldest first)
                    return list(reversed(result))
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            return []

    async def save_message(self, chat_id: int, role: str, content: str):
        """Save a single message"""
        if not self.pool:
            return

        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        INSERT INTO chat_history (chat_id, role, content) 
                        VALUES (%s, %s, %s)
                    """, (chat_id, role, content))
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            
    async def clear_history(self, chat_id: int):
        """Clear history for a chat"""
        if not self.pool:
            return

        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("DELETE FROM chat_history WHERE chat_id = %s", (chat_id,))
        except Exception as e:
            logger.error(f"Error clearing history: {e}")

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
