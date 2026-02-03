"""
Long-term and short-term memory management for personas.
Uses SQLite for persistence with encryption for sensitive data.
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from cryptography.fernet import Fernet
from loguru import logger


@dataclass
class MemoryEntry:
    """Single memory entry"""
    id: Optional[int] = None
    conversation_id: str = ""
    memory_type: str = "short_term"  # short_term, long_term, extracted_ioc
    content: str = ""
    timestamp: datetime = None
    importance: float = 0.5  # 0-1 scale for retention priority
    metadata: Dict = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class MemoryManager:
    """
    Manages conversation memory with automatic summarization
    and encrypted storage for sensitive extraction data.
    """
    
    def __init__(self, db_path: str = "data/ghostwire.db", encryption_key: Optional[bytes] = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate or use provided encryption key
        if encryption_key is None:
            encryption_key = Fernet.generate_key()
        self.cipher = Fernet(encryption_key)
        
        self._local = threading.local()
        self._init_database()
        
        logger.info(f"MemoryManager initialized with database: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Thread-safe connection handling"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def _init_database(self) -> None:
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT UNIQUE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                importance REAL DEFAULT 0.5,
                metadata TEXT,
                encrypted BOOLEAN DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation 
            ON memories(conversation_id, memory_type)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_context (
                conversation_id TEXT PRIMARY KEY,
                persona_id TEXT,
                current_state TEXT,
                summary TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
    
    def store(self, entry: MemoryEntry, encrypt: bool = False) -> int:
        """
        Store memory entry. Encrypt if contains sensitive IOCs.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        content = entry.content
        if encrypt:
            content = self.cipher.encrypt(content.encode()).decode()
        
        content_hash = hashlib.sha256(
            f"{entry.conversation_id}:{entry.content}:{entry.timestamp}".encode()
        ).hexdigest()
        
        try:
            cursor.execute("""
                INSERT INTO memories 
                (conversation_id, memory_type, content, content_hash, importance, metadata, encrypted)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.conversation_id,
                entry.memory_type,
                content,
                content_hash,
                entry.importance,
                json.dumps(entry.metadata),
                int(encrypt)
            ))
            conn.commit()
            return cursor.lastrowid
            
        except sqlite3.IntegrityError:
            logger.debug(f"Duplicate memory entry ignored: {content_hash[:8]}")
            return -1
    
    def retrieve(
        self, 
        conversation_id: str, 
        memory_type: Optional[str] = None,
        limit: int = 50,
        decrypt: bool = True
    ) -> List[MemoryEntry]:
        """Retrieve memories for conversation"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute("""
                SELECT * FROM memories 
                WHERE conversation_id = ? AND memory_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (conversation_id, memory_type, limit))
        else:
            cursor.execute("""
                SELECT * FROM memories 
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (conversation_id, limit))
        
        entries = []
        for row in cursor.fetchall():
            content = row['content']
            if decrypt and row['encrypted']:
                content = self.cipher.decrypt(content.encode()).decode()
            
            entries.append(MemoryEntry(
                id=row['id'],
                conversation_id=row['conversation_id'],
                memory_type=row['memory_type'],
                content=content,
                timestamp=datetime.fromisoformat(row['timestamp']),
                importance=row['importance'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            ))
        
        return entries
    
    def get_conversation_summary(self, conversation_id: str) -> str:
        """Get or generate conversation summary"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT summary FROM conversation_context 
            WHERE conversation_id = ?
        """, (conversation_id,))
        
        row = cursor.fetchone()
        if row and row['summary']:
            return row['summary']
        
        # Generate summary from recent memories
        memories = self.retrieve(conversation_id, limit=20)
        if not memories:
            return "New conversation"
        
        summary_points = [m.content[:100] for m in memories[:5]]
        return " | ".join(summary_points)
    
    def update_context(
        self, 
        conversation_id: str, 
        persona_id: str,
        current_state: str,
        summary: Optional[str] = None
    ) -> None:
        """Update conversation context"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO conversation_context 
            (conversation_id, persona_id, current_state, summary, last_updated)
            VALUES (?, ?, ?, ?, ?)
        """, (
            conversation_id,
            persona_id,
            current_state,
            summary or "",
            datetime.now()
        ))
        conn.commit()
    
    def cleanup_old_memories(self, days: int = 30) -> int:
        """Remove old short-term memories, keep long-term and IOCs"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            DELETE FROM memories 
            WHERE memory_type = 'short_term' 
            AND timestamp < ?
        """, (cutoff,))
        
        deleted = cursor.rowcount
        conn.commit()
        
        logger.info(f"Cleaned up {deleted} old memory entries")
        return deleted
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT memory_type, COUNT(*) as count 
            FROM memories 
            GROUP BY memory_type
        """)
        
        stats = {"total": 0, "by_type": {}}
        for row in cursor.fetchall():
            stats["by_type"][row['memory_type']] = row['count']
            stats["total"] += row['count']
        
        return stats
    
    def close(self) -> None:
        """Close database connections"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None