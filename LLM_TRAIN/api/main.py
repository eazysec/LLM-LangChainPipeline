"""
Application FastAPI principale pour le chatbot RAG.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any
import uvicorn

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import yaml

# Import des routes
from .routes.qa import router as qa_router
from .routes.admin import router as admin_router
from .routes.upload import router as upload_router

# Import des services
from .services.rag_service import RAGService

logger = logging.getLogger(__name__)

# Variables globales pour les services
rag_service: RAGService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire du cycle de vie de l'application."""
    # Startup
    logger.info("Initialisation de l'application...")
    
    try:
        # Charger la configuration
        config = load_config()
        
        # Initialiser le service RAG
        global rag_service
        rag_service = RAGService(config)
        await rag_service.initialize()
        
        # Stocker dans l'état de l'application
        app.state.rag_service = rag_service
        app.state.config = config
        
        logger.info("Application initialisée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Arrêt de l'application...")
    if rag_service:
        await rag_service.cleanup()


def load_config() -> Dict[str, Any]:
    """Charge la configuration depuis le fichier YAML."""
    config_path = os.getenv('CONFIG_PATH', 'configs/settings.yaml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration chargée depuis {config_path}")
        return config
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la config: {e}")
        # Configuration par défaut
        return {
            'app': {'host': '0.0.0.0', 'port': 8000},
            'models': {
                'ollama': {'base_url': 'http://100.64.0.34:11434', 'model_name': 'qwen2.5:latest'},
                'embeddings': {'model_name': 'sentence-transformers/all-MiniLM-L6-v2'}
            }
        }


def create_app() -> FastAPI:
    """Crée et configure l'application FastAPI."""
    
    app = FastAPI(
        title="ChatBot RAG API",
        description="API pour chatbot avec système RAG (Retrieval-Augmented Generation)",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Configuration CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # À restreindre en production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Inclure les routes
    app.include_router(qa_router, prefix="/api/v1", tags=["Questions & Réponses"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Administration"])
    app.include_router(upload_router, prefix="/api/v1", tags=["Upload"])
    
    # Route de base pour vérifier le statut
    @app.get("/")
    async def root():
        return {
            "message": "ChatBot RAG API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs"
        }
    
    @app.get("/health")
    async def health_check():
        """Endpoint de vérification de santé."""
        try:
            if hasattr(app.state, 'rag_service') and app.state.rag_service:
                status = await app.state.rag_service.health_check()
                return {"status": "healthy", "details": status}
            else:
                return {"status": "initializing"}
        except Exception as e:
            logger.error(f"Erreur health check: {e}")
            raise HTTPException(status_code=503, detail="Service unavailable")
    
    # Servir les fichiers statiques (UI)
    # ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "static")
    ui_path = os.path.join(os.path.dirname(__file__), "..", "static")
    if os.path.exists(ui_path):
        app.mount("/static", StaticFiles(directory=ui_path), name="static")
        
        @app.get("/ui")
        async def serve_ui():
            """Sert l'interface utilisateur RAG Interactive depuis simple_main_with_ui."""
            try:
                from .simple_main_with_ui import HTML_INTERFACE
                return HTMLResponse(content=HTML_INTERFACE)
            except ImportError as e:
                logger.warning(f"Impossible d'importer HTML_INTERFACE: {e}")
                # Fallback: essayer de servir depuis les fichiers statiques
                ui_file = os.path.join(ui_path, "index.html")
                if os.path.exists(ui_file):
                    return FileResponse(ui_file)
                else:
                    return {"message": "Interface utilisateur non disponible"}
        
        @app.get("/chat")
        async def serve_chat_ui():
            """Route alternative pour l'interface de chat."""
            try:
                from .simple_main_with_ui import HTML_INTERFACE
                return HTMLResponse(content=HTML_INTERFACE)
            except ImportError:
                # Rediriger vers /ui si l'import échoue
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url="/ui")
    
    return app


# Créer l'instance de l'application
app = create_app()


def get_rag_service() -> RAGService:
    """Récupère le service RAG depuis l'état de l'application."""
    if hasattr(app.state, 'rag_service') and app.state.rag_service:
        return app.state.rag_service
    else:
        raise HTTPException(status_code=503, detail="Service RAG non initialisé")


if __name__ == "__main__":
    # Configuration pour le développement
    config = load_config()
    app_config = config.get('app', {})
    
    uvicorn.run(
        "api.main:app",
        host=app_config.get('host', '0.0.0.0'),
        port=app_config.get('port', 8000),
        reload=True,
        log_level="info"
    ) 