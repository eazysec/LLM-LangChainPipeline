"""
Module LLM pour la génération de réponses dans le système RAG.
Gère les connexions aux modèles de génération (Ollama, OpenAI, etc.).
"""

from .ollama_client import OllamaClient
from .chain_builder import RAGChainBuilder
from .web_search import WebSearchClient

__all__ = ["OllamaClient", "RAGChainBuilder", "WebSearchClient"] 