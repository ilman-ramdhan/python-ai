import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from bot.services.storage_service import StorageService
from bot.core.config import BotConfig

@pytest.fixture
def mock_config():
    return BotConfig(
        bot_token="test",
        groq_api_key="test",
        db_host="localhost",
        db_port=3306,
        db_user="root",
        db_password="password",
        db_name="test_db"
    )

@pytest.mark.asyncio
async def test_service_instantiation(mock_config):
    """Test that service can be instantiated"""
    service = StorageService(mock_config)
    assert service.config == mock_config
    assert service.pool is None
