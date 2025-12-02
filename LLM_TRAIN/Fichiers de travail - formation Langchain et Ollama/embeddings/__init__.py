"""
Module de gestion des embeddings vectoriels pour le système RAG.
Gère la génération des vecteurs et la construction des index.
"""

from .embedding_model import EmbeddingModel
from .build_index import VectorIndexBuilder
from .utils import normalize_embeddings, cosine_similarity, batch_encode

__all__ = ["EmbeddingModel", "VectorIndexBuilder", "normalize_embeddings", "cosine_similarity", "batch_encode"] 