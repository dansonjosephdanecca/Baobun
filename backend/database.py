import sqlite3
import json
from datetime import datetime
from typing import List, Optional
import asyncio
import aiosqlite
from models import ChatMessage, ConversationHistory, MessageRole
import uuid

class Database:
    def __init__(self, db_path: str = "data/conversations.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP,
                requires_search BOOLEAN,
                search_results TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

        conn.commit()
        conn.close()

    async def create_conversation(self) -> str:
        """Create a new conversation and return its ID"""
        conversation_id = str(uuid.uuid4())
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO conversations (id, created_at, updated_at) VALUES (?, ?, ?)",
                (conversation_id, datetime.now(), datetime.now())
            )
            await db.commit()
        return conversation_id

    async def save_message(self, conversation_id: str, message: ChatMessage):
        """Save a message to the database"""
        async with aiosqlite.connect(self.db_path) as db:
            # Ensure conversation exists
            cursor = await db.execute(
                "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
            )
            if not await cursor.fetchone():
                await db.execute(
                    "INSERT INTO conversations (id, created_at, updated_at) VALUES (?, ?, ?)",
                    (conversation_id, datetime.now(), datetime.now())
                )

            # Save message
            search_results_json = json.dumps(message.search_results) if message.search_results else None
            await db.execute(
                """INSERT INTO messages
                   (conversation_id, role, content, timestamp, requires_search, search_results)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    conversation_id,
                    message.role.value,
                    message.content,
                    message.timestamp,
                    message.requires_search,
                    search_results_json
                )
            )

            # Update conversation timestamp
            await db.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (datetime.now(), conversation_id)
            )
            await db.commit()

    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[ChatMessage]:
        """Retrieve conversation history"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM messages
                   WHERE conversation_id = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (conversation_id, limit)
            )
            rows = await cursor.fetchall()

            messages = []
            for row in reversed(rows):
                search_results = json.loads(row["search_results"]) if row["search_results"] else None
                messages.append(ChatMessage(
                    role=MessageRole(row["role"]),
                    content=row["content"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    requires_search=bool(row["requires_search"]),
                    search_results=search_results
                ))

            return messages

    async def get_all_conversations(self) -> List[dict]:
        """Get all conversation summaries"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT c.*,
                   (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as message_count,
                   (SELECT content FROM messages WHERE conversation_id = c.id ORDER BY timestamp DESC LIMIT 1) as last_message
                   FROM conversations c
                   ORDER BY updated_at DESC"""
            )
            rows = await cursor.fetchall()

            return [dict(row) for row in rows]

    async def delete_conversation(self, conversation_id: str):
        """Delete a conversation and all its messages"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            await db.commit()