"""
Schémas Pydantic pour les endpoints d'administration.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ModelInfo(BaseModel):
    """Informations sur un modèle."""
    name: str = Field(..., description="Nom du modèle")
    available: bool = Field(..., description="Disponibilité du modèle")
    size: Optional[str] = Field(default=None, description="Taille du modèle")
    modified: Optional[datetime] = Field(default=None, description="Date de modification")


class IndexStats(BaseModel):
    """Statistiques de l'index vectoriel."""
    total_documents: int = Field(..., description="Nombre total de documents")
    total_chunks: int = Field(..., description="Nombre total de chunks")
    index_size: Optional[str] = Field(default=None, description="Taille de l'index")
    last_updated: Optional[datetime] = Field(default=None, description="Dernière mise à jour")


class SystemStatus(BaseModel):
    """Statut global du système."""
    status: str = Field(..., description="Statut général (healthy/degraded/down)")
    version: str = Field(..., description="Version de l'application")
    uptime: float = Field(..., description="Temps de fonctionnement en secondes")
    
    # Statuts des composants
    llm_status: bool = Field(..., description="Statut du modèle LLM")
    embedding_status: bool = Field(..., description="Statut du modèle d'embeddings")
    vector_db_status: bool = Field(..., description="Statut de la base vectorielle")
    web_search_status: bool = Field(..., description="Statut de la recherche web")
    
    # Informations sur les modèles
    llm_info: ModelInfo = Field(..., description="Informations sur le modèle LLM")
    embedding_info: Dict[str, Any] = Field(..., description="Informations sur les embeddings")
    
    # Statistiques de l'index
    index_stats: IndexStats = Field(..., description="Statistiques de l'index")
    
    # Configuration
    config: Dict[str, Any] = Field(..., description="Configuration actuelle")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.0,
                "llm_status": True,
                "embedding_status": True,
                "vector_db_status": True,
                "web_search_status": True,
                "llm_info": {
                    "name": "qwen2.5:latest",
                    "available": True,
                    "size": "7.4GB",
                    "modified": "2024-01-01T10:00:00Z"
                },
                "embedding_info": {
                    "model_name": "all-MiniLM-L6-v2",
                    "dimension": 384
                },
                "index_stats": {
                    "total_documents": 150,
                    "total_chunks": 2500,
                    "index_size": "250MB",
                    "last_updated": "2024-01-01T10:00:00Z"
                },
                "config": {
                    "rag": {
                        "chunk_size": 500,
                        "top_k": 5
                    }
                }
            }
        }


class LogEntry(BaseModel):
    """Entrée de log."""
    timestamp: datetime = Field(..., description="Horodatage")
    level: str = Field(..., description="Niveau de log")
    logger: str = Field(..., description="Nom du logger")
    message: str = Field(..., description="Message")


class LogsResponse(BaseModel):
    """Réponse pour les logs."""
    total_entries: int = Field(..., description="Nombre total d'entrées")
    entries: List[LogEntry] = Field(..., description="Entrées de log")
    page: int = Field(..., description="Page actuelle")
    per_page: int = Field(..., description="Entrées par page")


class ConfigUpdate(BaseModel):
    """Mise à jour de configuration."""
    section: str = Field(..., description="Section de configuration")
    key: str = Field(..., description="Clé de configuration")
    value: Any = Field(..., description="Nouvelle valeur")
    
    class Config:
        schema_extra = {
            "example": {
                "section": "rag",
                "key": "chunk_size",
                "value": 600
            }
        }


class ConfigResponse(BaseModel):
    """Réponse de configuration."""
    success: bool = Field(..., description="Indique si la mise à jour a réussi")
    message: str = Field(..., description="Message de statut")
    old_value: Any = Field(..., description="Ancienne valeur")
    new_value: Any = Field(..., description="Nouvelle valeur")


class RebuildIndexRequest(BaseModel):
    """Requête pour reconstruire l'index."""
    force: bool = Field(default=False, description="Forcer la reconstruction")
    clear_existing: bool = Field(default=False, description="Vider l'index existant")


class RebuildIndexResponse(BaseModel):
    """Réponse de reconstruction d'index."""
    success: bool = Field(..., description="Indique si la reconstruction a réussi")
    message: str = Field(..., description="Message de statut")
    documents_processed: int = Field(..., description="Nombre de documents traités")
    chunks_created: int = Field(..., description="Nombre de chunks créés")
    processing_time: float = Field(..., description="Temps de traitement")


class IndexRebuildRequest(RebuildIndexRequest):
    """Alias pour compatibilité ascendante."""
    pass


class IndexRebuildResponse(RebuildIndexResponse):
    """Alias pour compatibilité ascendante."""
    pass


class MetricsResponse(BaseModel):
    """Métriques du système."""
    queries_total: int = Field(..., description="Nombre total de requêtes")
    queries_per_hour: float = Field(..., description="Requêtes par heure")
    average_response_time: float = Field(..., description="Temps de réponse moyen")
    success_rate: float = Field(..., description="Taux de succès (%)")
    web_search_usage: float = Field(..., description="Utilisation de la recherche web (%)")
    
    # Métriques de performance
    memory_usage: float = Field(..., description="Utilisation mémoire (MB)")
    cpu_usage: float = Field(..., description="Utilisation CPU (%)")
    
    class Config:
        schema_extra = {
            "example": {
                "queries_total": 1250,
                "queries_per_hour": 45.2,
                "average_response_time": 2.3,
                "success_rate": 96.8,
                "web_search_usage": 15.2,
                "memory_usage": 1024.5,
                "cpu_usage": 35.2
            }
        } 