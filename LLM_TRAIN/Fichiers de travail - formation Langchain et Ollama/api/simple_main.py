"""
Version simplifiée de l'API pour test rapide.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os

app = FastAPI(
    title="ChatBot RAG API (Version Simple)",
    description="API simplifiée pour test rapide",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic simples
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    confidence: float = 0.8
    sources: List[Dict] = []

# Routes simples
@app.get("/")
async def root():
    return {
        "message": "ChatBot RAG API (Version Simple)",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "simple"}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint de chat simplifié."""
    return ChatResponse(
        answer=f"Réponse simulée à: '{request.message}'. Cette version n'a pas encore Ollama configuré.",
        session_id=request.session_id or "demo_session",
        confidence=0.8,
        sources=[
            {
                "filename": "demo.txt",
                "content": "Contenu d'exemple",
                "similarity": 0.9
            }
        ]
    )

@app.get("/api/v1/admin/status")
async def admin_status():
    return {
        "status": "healthy",
        "version": "simple",
        "components": {
            "api": True,
            "llm": False,  # Pas encore configuré
            "embeddings": False,
            "vector_db": False
        },
        "message": "Version simplifiée - Ollama pas encore configuré"
    }

# Servir l'interface web
@app.get("/chat")
async def serve_chat_ui():
    """Interface de chat web."""
    from fastapi.responses import HTMLResponse
    
    # Lecture du contenu HTML
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="""
        <h1>Interface en cours de chargement...</h1>
        <p>Veuillez réessayer dans quelques instants.</p>
        <p><a href="/docs">Documentation API</a></p>
        """)

# Route alternative pour l'interface
@app.get("/ui")
async def serve_ui_alt():
    """Interface alternative."""
    return await serve_chat_ui()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 