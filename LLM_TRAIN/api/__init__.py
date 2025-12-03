"""
API REST pour le chatbot RAG.
Expose les services via FastAPI.
"""

from .main import app
from .services.rag_service import RAGService
from .schemas import ChatRequest, ChatResponse

__all__ = ["app", "RAGService", "ChatRequest", "ChatResponse"] 