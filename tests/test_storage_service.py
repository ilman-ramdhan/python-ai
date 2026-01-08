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
async def test_initialize(mock_config):
    """Test that connection pool is created on initialize"""
    with patch("bot.services.storage_service.aiomysql.create_pool", new_callable=AsyncMock) as mock_create_pool:
        # returns an AsyncContextManager mock for pool.acquire()
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Setup context managers
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
        
        mock_create_pool.return_value = mock_pool

        service = StorageService(mock_config)
        await service.initialize()
        
        mock_create_pool.assert_called_once_with(
            host=mock_config.db_host,
            port=mock_config.db_port,
            user=mock_config.db_user,
            password=mock_config.db_password,
            db=mock_config.db_name,
            autocommit=True
        )
        
        # Ensure table creation query run
        # Ensure table creation query run
        # Depending on how create_pool is mocked, we need to check the context manager chain
        mock_cursor.execute.assert_called()
        assert "CREATE TABLE IF NOT EXISTS" in str(mock_cursor.execute.call_args)

@pytest.mark.asyncio
async def test_save_message_success(mock_config):
    """Test saving a message uses correct SQL"""
    service = StorageService(mock_config)
    
    # Mock the pool directly
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Wire up async context managers
    mock_pool.acquire = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock()
    
    mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__aexit__ = AsyncMock()
    
    service.pool = mock_pool

    await service.save_message(123, "user", "hello")
    
    mock_cursor.execute.assert_called_once()
    # Check arguments loosely as call_args parsing on mocks can be tricky
    sql = str(mock_cursor.execute.call_args)
    assert "INSERT INTO chat_history" in sql
    assert str(123) in sql
    assert "user" in sql
    assert "hello" in sql

@pytest.mark.asyncio
async def test_get_history(mock_config):
    """Test fetching history returns formatted list"""
    service = StorageService(mock_config)
    
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    
    # Setup fetchall return
    mock_cursor.fetchall = AsyncMock(return_value=[
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"}
    ])
    
    mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
    
    service.pool = mock_pool

    history = await service.get_chat_history(123, limit=2)
    
    # verify it reverses the result (as per implementation which does list(reversed(result)))
    # Wait, the implementation does reversed(result) where result is ORDER BY id DESC (newest first).
    # So reversed makes it oldest first.
    assert len(history) == 2
    assert history[0]["role"] == "assistant" # reversed(["user", "assistant"]) -> "assistant", "user"?
    # Let's check impl: 
    # Query: ORDER BY id DESC (Newest, Older) -> [New, Old]
    # Code: list(reversed(result)) -> [Old, New]
    # Mock data [User(Hi), Assistant(Hello)] is irrelevant order unless we assume it came from DB.
    # If DB returned [Assistant(Hello), User(Hi)] (Newest first), then reversed is [User, Assistant] (Chronological)
    
    # Just asserting call for now
    # Just asserting call for now
    mock_cursor.execute.assert_called_once()
    assert "SELECT role, content" in str(mock_cursor.execute.call_args)
