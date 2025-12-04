"""
Routes d'administration du système.
"""

import logging
import os
import yaml
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ..services.rag_service import RAGService
from ..schemas.admin import (
    SystemStatus, IndexStats, LogEntry, ConfigUpdate, 
    IndexRebuildRequest, IndexRebuildResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_rag_service() -> RAGService:
    """Dependency pour obtenir le service RAG."""
    from ..main import rag_service
    return rag_service


@router.get("/status", response_model=SystemStatus)
async def get_system_status(rag_service: RAGService = Depends(get_rag_service)):
    """
    Récupère le statut général du système.
    
    Args:
        rag_service: Service RAG
        
    Returns:
        Statut du système
    """
    try:
        health_data = await rag_service.health_check()
        metrics = rag_service.get_metrics()
        
        return SystemStatus(
            status=health_data["overall_status"],
            uptime=health_data["uptime"],
            components=health_data["components"],
            metrics={
                "total_queries": metrics["total_queries"],
                "success_rate": metrics["success_rate"],
                "average_response_time": metrics["average_response_time"],
                "active_conversations": metrics["active_conversations"]
            }
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/stats", response_model=IndexStats)
async def get_index_stats(rag_service: RAGService = Depends(get_rag_service)):
    """
    Récupère les statistiques de l'index vectoriel.
    
    Args:
        rag_service: Service RAG
        
    Returns:
        Statistiques de l'index
    """
    try:
        # TODO: Implémenter la récupération des vraies statistiques
        # Pour l'instant, retourner des données simulées
        return IndexStats(
            total_documents=150,
            total_chunks=3750,
            index_size_mb=45.2,
            last_updated="2024-01-15T14:30:00",
            embedding_dimensions=384
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/logs")
async def get_logs(
    level: str = Query("INFO", description="Niveau de log (DEBUG, INFO, WARNING, ERROR)"),
    limit: int = Query(100, description="Nombre de logs à retourner"),
    offset: int = Query(0, description="Décalage pour la pagination")
):
    """
    Récupère les logs du système.
    
    Args:
        level: Niveau de log à filtrer
        limit: Nombre de logs à retourner
        offset: Décalage pour la pagination
        
    Returns:
        Liste des logs
    """
    try:
        # TODO: Implémenter la récupération des vrais logs
        # Pour l'instant, retourner des logs simulés
        logs = [
            LogEntry(
                timestamp=f"2024-01-15T{10+i:02d}:30:00",
                level="INFO",
                message=f"Message de log simulé {i}",
                component="rag_service"
            )
            for i in range(offset, min(offset + limit, 50))
        ]
        
        return {
            "logs": logs,
            "total": 50,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des logs: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/config")
async def get_config():
    """
    Récupère la configuration actuelle du système.
    
    Returns:
        Configuration du système
    """
    try:
        config_path = "configs/settings.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        else:
            raise HTTPException(status_code=404, detail="Fichier de configuration non trouvé")
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la config: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.put("/config")
async def update_config(
    config_update: ConfigUpdate,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Met à jour la configuration du système.
    
    Args:
        config_update: Nouvelle configuration
        rag_service: Service RAG
        
    Returns:
        Confirmation de mise à jour
    """
    try:
        config_path = "configs/settings.yaml"
        
        # Charger la configuration actuelle
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f)
        else:
            current_config = {}
        
        # Mettre à jour avec les nouvelles valeurs
        updated_config = {**current_config, **config_update.config}
        
        # Sauvegarder la nouvelle configuration
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(updated_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info("Configuration mise à jour")
        
        return JSONResponse({
            "success": True,
            "message": "Configuration mise à jour avec succès",
            "restart_required": True
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la config: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.post("/index/rebuild", response_model=IndexRebuildResponse)
async def rebuild_index(
    request: IndexRebuildRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Reconstruit l'index vectoriel.
    
    Args:
        request: Paramètres de reconstruction
        rag_service: Service RAG
        
    Returns:
        Résultat de la reconstruction
    """
    try:
        # TODO: Implémenter la vraie reconstruction d'index
        # Pour l'instant, simuler l'opération
        logger.info(f"Début de reconstruction d'index: {request.index_type}")
        
        # Simuler un temps de traitement
        import asyncio
        await asyncio.sleep(0.5)
        
        return IndexRebuildResponse(
            success=True,
            message="Index reconstruit avec succès",
            rebuild_time=2.5,
            documents_processed=150,
            chunks_created=3750
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la reconstruction d'index: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.delete("/index/clear")
async def clear_index(rag_service: RAGService = Depends(get_rag_service)):
    """
    Vide complètement l'index vectoriel.
    
    Args:
        rag_service: Service RAG
        
    Returns:
        Confirmation de suppression
    """
    try:
        # TODO: Implémenter la vraie suppression d'index
        logger.warning("Suppression complète de l'index demandée")
        
        return JSONResponse({
            "success": True,
            "message": "Index vidé avec succès",
            "documents_removed": 150,
            "chunks_removed": 3750
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'index: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/metrics")
async def get_detailed_metrics(rag_service: RAGService = Depends(get_rag_service)):
    """
    Récupère des métriques détaillées du système.
    
    Args:
        rag_service: Service RAG
        
    Returns:
        Métriques détaillées
    """
    try:
        metrics = rag_service.get_metrics()
        health_data = await rag_service.health_check()
        
        detailed_metrics = {
            "performance": {
                "total_queries": metrics["total_queries"],
                "successful_queries": metrics["successful_queries"],
                "failed_queries": metrics["failed_queries"],
                "success_rate": metrics["success_rate"],
                "average_response_time": metrics["average_response_time"],
                "queries_per_hour": metrics["queries_per_hour"]
            },
            "usage": {
                "web_search_usage": metrics["web_search_usage"],
                "active_conversations": metrics["active_conversations"],
                "last_query_time": metrics["last_query_time"]
            },
            "system": {
                "uptime": health_data["uptime"],
                "components_status": health_data["components"]
            }
        }
        
        return detailed_metrics
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des métriques: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.post("/restart")
async def restart_system():
    """
    Redémarre le système (simulation).
    
    Returns:
        Confirmation de redémarrage
    """
    try:
        # TODO: Implémenter un vrai redémarrage gracieux
        logger.info("Redémarrage du système demandé")
        
        return JSONResponse({
            "success": True,
            "message": "Redémarrage du système en cours..."
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du redémarrage: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/health")
async def health_check(rag_service: RAGService = Depends(get_rag_service)):
    """
    Vérification de santé rapide pour les outils de monitoring.
    
    Args:
        rag_service: Service RAG
        
    Returns:
        Statut de santé
    """
    try:
        health_data = await rag_service.health_check()
        
        if health_data["overall_status"] == "healthy":
            return JSONResponse({"status": "healthy"}, status_code=200)
        elif health_data["overall_status"] == "degraded":
            return JSONResponse({"status": "degraded"}, status_code=200)
        else:
            return JSONResponse({"status": "unhealthy"}, status_code=503)
            
    except Exception as e:
        logger.error(f"Erreur lors du health check: {e}")
        return JSONResponse({"status": "error", "error": str(e)}, status_code=503) 