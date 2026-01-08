import json
import asyncio
import os
import aiomysql
from pathlib import Path
from dotenv import load_dotenv

async def migrate():
    """Migrate data from conversation_history.json to MySQL"""
    
    # 1. Load Env
    load_dotenv()
    
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "telegram_bot")

    # 2. Check JSON file
    json_path = Path("conversation_history.json")
    if not json_path.exists():
        print("❌ conversation_history.json not found!")
        return

    print(f"📂 Reading {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("❌ Invalid JSON file")
            return

    # 3. Connect to DB
    print(f"🔌 Connecting to MySQL ({db_host}:{db_port})...")
    try:
        pool = await aiomysql.create_pool(
            host=db_host, 
            port=db_port, 
            user=db_user, 
            password=db_password, 
            db=db_name,
            autocommit=True
        )
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # 4. Create table if not exists (Safety check)
    async with pool.acquire() as conn:
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

            # 5. Insert Data
            count = 0
            print("🚀 Migrating messages...")
            
            for chat_id_str, messages in data.items():
                chat_id = int(chat_id_str)
                for msg in messages:
                    role = msg.get("role")
                    content = msg.get("content")
                    
                    if role and content:
                        await cur.execute("""
                            INSERT INTO chat_history (chat_id, role, content)
                            VALUES (%s, %s, %s)
                        """, (chat_id, role, content))
                        count += 1
            
            print(f"✅ Migration successful! Transferred {count} messages.")

    pool.close()
    await pool.wait_closed()

if __name__ == "__main__":
    asyncio.run(migrate())
