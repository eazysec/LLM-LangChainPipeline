"""
Schémas Pydantic pour les endpoints de chat.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    """Message dans une conversation."""
    role: str = Field(..., description="Rôle du message (user/assistant)")
    content: str = Field(..., description="Contenu du message")
    timestamp: Optional[datetime] = Field(default=None, description="Horodatage du message")


class ConversationHistory(BaseModel):
    """Historique de conversation."""
    messages: List[Message] = Field(default=[], description="Liste des messages")
    session_id: Optional[str] = Field(default=None, description="ID de session")


class ChatRequest(BaseModel):
    """Requête de chat."""
    message: str = Field(..., description="Message de l'utilisateur", min_length=1)
    conversation_history: Optional[List[Message]] = Field(
        default=[], 
        description="Historique de conversation"
    )
    session_id: Optional[str] = Field(default=None, description="ID de session")
    use_web_search: Optional[bool] = Field(
        default=None, 
        description="Forcer/empêcher la recherche web"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Filtres pour la recherche de documents"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Comment installer Python sur Ubuntu?",
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "Bonjour, j'ai besoin d'aide",
                        "timestamp": "2024-01-01T10:00:00Z"
                    },
                    {
                        "role": "assistant", 
                        "content": "Bonjour ! Je suis là pour vous aider.",
                        "timestamp": "2024-01-01T10:00:01Z"
                    }
                ],
                "session_id": "session_123",
                "use_web_search": True
            }
        }


class SourceInfo(BaseModel):
    """Informations sur une source."""
    chunk_id: str = Field(..., description="ID du chunk")
    filename: Optional[str] = Field(default=None, description="Nom du fichier source")
    similarity: float = Field(..., description="Score de similarité")
    content_preview: str = Field(..., description="Aperçu du contenu")


class WebResultInfo(BaseModel):
    """Informations sur un résultat web."""
    title: str = Field(..., description="Titre de la page")
    url: str = Field(..., description="URL de la page")
    snippet: str = Field(..., description="Extrait de la page")


class ChatResponse(BaseModel):
    """Réponse de chat."""
    answer: str = Field(..., description="Réponse générée")
    sources: List[SourceInfo] = Field(default=[], description="Sources utilisées")
    web_results: List[WebResultInfo] = Field(default=[], description="Résultats web")
    confidence: float = Field(..., description="Confiance dans la réponse (0-1)")
    response_time: float = Field(..., description="Temps de traitement en secondes")
    session_id: str = Field(..., description="ID de session")
    metadata: Dict[str, Any] = Field(default={}, description="Métadonnées supplémentaires")
    
    class Config:
        schema_extra = {
            "example": {
                "answer": "Pour installer Python sur Ubuntu, vous pouvez utiliser apt...",
                "sources": [
                    {
                        "chunk_id": "doc1_chunk1",
                        "filename": "python_installation.pdf",
                        "similarity": 0.95,
                        "content_preview": "Installation de Python sur Ubuntu..."
                    }
                ],
                "web_results": [
                    {
                        "title": "How to Install Python on Ubuntu",
                        "url": "https://example.com/python-ubuntu",
                        "snippet": "This guide shows you how to install Python..."
                    }
                ],
                "confidence": 0.92,
                "response_time": 1.5,
                "session_id": "session_123",
                "metadata": {
                    "model_used": "qwen2.5:latest",
                    "web_search_used": True
                }
            }
        }


class StreamChatRequest(BaseModel):
    """Requête pour le chat en streaming."""
    message: str = Field(..., description="Message de l'utilisateur")
    conversation_history: Optional[List[Message]] = Field(default=[], description="Historique")
    session_id: Optional[str] = Field(default=None, description="ID de session")


class StreamChatChunk(BaseModel):
    """Chunk de réponse en streaming."""
    content: str = Field(..., description="Contenu du chunk")
    is_final: bool = Field(default=False, description="Indique si c'est le dernier chunk")
    session_id: str = Field(..., description="ID de session")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Métadonnées finales") 