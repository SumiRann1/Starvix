import asyncio
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent / "chatbot.db"
if not DB_PATH.parent.exists():
    DB_PATH.parent.mkdir(exist_ok=True)

async def create_db():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.cursor()

        await cursor.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            thread_id TEXT NOT NULL,    
            model TEXT NOT NULL, 
            role TEXT NOT NULL, 
            content TEXT NOT NULL, 
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP 
        )""")

        await db.commit()
        print("✅ Database and table created successfully.")

    

        
if __name__ == "__main__":
    asyncio.run(create_db())

        
        
        