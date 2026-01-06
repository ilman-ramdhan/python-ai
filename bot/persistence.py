import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger("bot.persistence")

class PersistenceManager:
    """Async persistence manager for conversation history"""

    def __init__(self, history_file: Path):
        self.history_file = history_file

    async def load_history(self) -> Dict[int, List[Dict[str, str]]]:
        """Load conversation history from disk asynchronously"""
        try:
            if not self.history_file.exists():
                return {}

            loop = asyncio.get_running_loop()
            # Run file I/O in a separate thread to avoid blocking the event loop
            data = await loop.run_in_executor(None, self._read_file)
            
            # Convert string keys back to integers (JSON stores keys as strings)
            history = {int(k): v for k, v in data.items()}
            logger.info(f"Loaded history for {len(history)} chats")
            return history
            
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return {}

    def _read_file(self) -> Dict[str, Any]:
        """Blocking file read - helper for run_in_executor"""
        with open(self.history_file, "r", encoding="utf-8") as f:
            return json.load(f)

    async def save_history(self, history: Dict[int, List[Dict[str, str]]]) -> None:
        """Save conversation history to disk asynchronously"""
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._write_file, history)
            logger.debug("History saved")
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def _write_file(self, history: Dict[int, List[Dict[str, str]]]) -> None:
        """Blocking file write - helper for run_in_executor"""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
