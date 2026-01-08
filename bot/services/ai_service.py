from typing import List, Dict, Optional, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from groq import AsyncGroq
from ..core.config import BotConfig

class AIService:
    """Async AI ServiceWrapper"""

    def __init__(self, config: BotConfig):
        self.config = config
        self.client = AsyncGroq(api_key=config.groq_api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def get_response(
        self, 
        messages: List[Dict[str, Any]], 
        model: Optional[str] = None
    ) -> str:
        """
        Call Groq API asynchronously
        
        Args:
            messages: List of conversation messages
            model: Optional model override (e.g. for vision)
            
        Returns:
            The AI response text
        """
        response = await self.client.chat.completions.create(
            messages=messages,
            model=model or self.config.ai_model,
            temperature=self.config.ai_temperature,
        )
        return response.choices[0].message.content
