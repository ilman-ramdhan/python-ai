import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.services.ai_service import AIService
from bot.core.config import BotConfig

@pytest.fixture
def mock_config():
    return BotConfig(
        bot_token="test_token",
        groq_api_key="test_key",
        admin_ids=[123]
    )

@pytest.mark.asyncio
async def test_get_response_success(mock_config):
    """Test successful AI response"""
    
    # Mock the AsyncGroq client
    with patch("bot.services.ai_service.AsyncGroq") as MockGroq:
        # Setup mock response chain
        mock_client = MockGroq.return_value
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="Hello world"))
        ]
        
        # Async method mocking
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        
        service = AIService(mock_config)
        response = await service.get_response([{"role": "user", "content": "Hi"}])
        
        assert response == "Hello world"
        mock_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_get_response_custom_model(mock_config):
    """Test model override logic"""
    
    with patch("bot.services.ai_service.AsyncGroq") as MockGroq:
        mock_client = MockGroq.return_value
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="Vision response"))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        
        service = AIService(mock_config)
        await service.get_response([], model="vision-model")
        
        # Verify call used the custom model
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "vision-model"
