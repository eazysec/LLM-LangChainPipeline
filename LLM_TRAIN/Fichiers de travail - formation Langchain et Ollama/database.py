"""
Base de données simple pour stocker les conversations et permettre au RAG d'apprendre.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager


class ConversationDB:
    """Gestionnaire de base de données pour les conversations."""
    
    def __init__(self, db_path: str = "data/conversations.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données."""
        with self.get_connection() as conn:
            # Table des conversations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    sources TEXT,
                    confidence REAL,
                    feedback INTEGER DEFAULT 0
                )
            """)
            
            # Créer les index séparément
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON conversations(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)")
            
            # Table des sessions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    title TEXT,
                    total_messages INTEGER DEFAULT 0
                )
            """)
            
            # Index pour la recherche full-text
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS conversation_search 
                USING fts5(
                    conversation_id,
                    user_message,
                    assistant_response
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager pour les connexions à la base de données."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_conversation(self, session_id: str, user_message: str, 
                         assistant_response: str, sources: List[Dict] = None,
                         confidence: float = None, metadata: Dict = None) -> str:
        """Sauvegarde une conversation."""
        conversation_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            # Sauvegarder la conversation
            conn.execute("""
                INSERT INTO conversations 
                (id, session_id, user_message, assistant_response, sources, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation_id,
                session_id,
                user_message,
                assistant_response,
                json.dumps(sources) if sources else None,
                confidence,
                json.dumps(metadata) if metadata else None
            ))
            
            # Mettre à jour la session
            conn.execute("""
                INSERT OR REPLACE INTO sessions 
                (session_id, last_activity, total_messages, title)
                VALUES (?, CURRENT_TIMESTAMP, 
                        COALESCE((SELECT total_messages FROM sessions WHERE session_id = ?), 0) + 1,
                        COALESCE((SELECT title FROM sessions WHERE session_id = ?), ?))
            """, (session_id, session_id, session_id, user_message[:50] + "..."))
            
            # Ajouter à l'index de recherche
            conn.execute("""
                INSERT INTO conversation_search 
                (conversation_id, user_message, assistant_response)
                VALUES (?, ?, ?)
            """, (conversation_id, user_message, assistant_response))
            
            conn.commit()
        
        return conversation_id
    
    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Récupère l'historique d'une session."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT user_message, assistant_response, timestamp, sources, confidence
                FROM conversations 
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (session_id, limit))
            
            history = []
            for row in cursor:
                history.extend([
                    {
                        "role": "user",
                        "content": row["user_message"],
                        "timestamp": row["timestamp"]
                    },
                    {
                        "role": "assistant", 
                        "content": row["assistant_response"],
                        "timestamp": row["timestamp"],
                        "sources": json.loads(row["sources"]) if row["sources"] else [],
                        "confidence": row["confidence"]
                    }
                ])
            
            return history
    
    def search_conversations(self, query: str, limit: int = 10) -> List[Dict]:
        """Recherche dans les conversations passées pour le RAG."""
        with self.get_connection() as conn:
            try:
                # Nettoyer et échapper la requête pour FTS5
                clean_query = query.replace('"', '').replace("'", "").replace("!", "").replace("?", "")
                if not clean_query.strip():
                    return []
                
                cursor = conn.execute("""
                    SELECT c.user_message, c.assistant_response, c.timestamp, c.confidence, 1 as rank
                    FROM conversation_search cs
                    JOIN conversations c ON cs.conversation_id = c.id
                    WHERE cs MATCH ?
                    ORDER BY c.timestamp DESC
                    LIMIT ?
                """, (f'"{clean_query}"', limit))
            except Exception as e:
                print(f"Erreur FTS5: {e}")
                # Fallback vers une recherche LIKE simple
                cursor = conn.execute("""
                    SELECT user_message, assistant_response, timestamp, confidence, 1 as rank
                    FROM conversations
                    WHERE user_message LIKE ? OR assistant_response LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (f'%{query}%', f'%{query}%', limit))
            
            results = []
            for row in cursor:
                results.append({
                    "user_question": row["user_message"],
                    "assistant_answer": row["assistant_response"],
                    "timestamp": row["timestamp"],
                    "confidence": row["confidence"],
                    "relevance": row["rank"]
                })
            
            return results
    
    def get_recent_conversations(self, days: int = 7, limit: int = 20) -> List[Dict]:
        """Récupère les conversations récentes pour l'apprentissage."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT user_message, assistant_response, confidence, timestamp
                FROM conversations 
                WHERE datetime(timestamp) >= datetime('now', '-{} days')
                AND confidence > 0.7
                ORDER BY timestamp DESC
                LIMIT ?
            """.format(days), (limit,))
            
            return [dict(row) for row in cursor]
    
    def get_sessions(self, limit: int = 20) -> List[Dict]:
        """Récupère la liste des sessions."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT session_id, title, total_messages, last_activity
                FROM sessions 
                ORDER BY last_activity DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor]
    
    def update_feedback(self, conversation_id: str, feedback: int):
        """Met à jour le feedback d'une conversation (1=positif, -1=négatif)."""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE conversations 
                SET feedback = ?
                WHERE id = ?
            """, (feedback, conversation_id))
            conn.commit()
    
    def get_conversation_stats(self) -> Dict:
        """Récupère des statistiques sur les conversations."""
        with self.get_connection() as conn:
            stats = {}
            
            # Nombre total de conversations
            cursor = conn.execute("SELECT COUNT(*) as total FROM conversations")
            stats["total_conversations"] = cursor.fetchone()["total"]
            
            # Nombre de sessions
            cursor = conn.execute("SELECT COUNT(*) as total FROM sessions")
            stats["total_sessions"] = cursor.fetchone()["total"]
            
            # Conversations aujourd'hui
            cursor = conn.execute("""
                SELECT COUNT(*) as today 
                FROM conversations 
                WHERE date(timestamp) = date('now')
            """)
            stats["conversations_today"] = cursor.fetchone()["today"]
            
            # Confiance moyenne
            cursor = conn.execute("""
                SELECT AVG(confidence) as avg_confidence 
                FROM conversations 
                WHERE confidence IS NOT NULL
            """)
            stats["average_confidence"] = cursor.fetchone()["avg_confidence"]
            
            return stats


# Instance globale
conversation_db = ConversationDB()


def init_conversation_db():
    """Initialise la base de données des conversations."""
    import os
    os.makedirs("data", exist_ok=True)
    global conversation_db
    conversation_db = ConversationDB()
    return conversation_db 