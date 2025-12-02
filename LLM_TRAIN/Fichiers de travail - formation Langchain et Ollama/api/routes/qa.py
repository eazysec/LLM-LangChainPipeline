"""
Routes pour les questions-réponses.
"""

import logging
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
import json

from ..schemas.chat import (
    ChatRequest, ChatResponse, StreamChatRequest, 
    SourceInfo, WebResultInfo, Message
)
from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_rag_service(request: Request) -> RAGService:
    """Dépendance pour récupérer le service RAG."""
    if hasattr(request.app.state, 'rag_service') and request.app.state.rag_service:
        return request.app.state.rag_service
    else:
        raise HTTPException(status_code=503, detail="Service RAG non disponible")


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    chat_request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> ChatResponse:
    """
    Endpoint principal de chat.
    
    Args:
        chat_request: Requête de chat
        rag_service: Service RAG
        
    Returns:
        Réponse du chatbot
    """
    try:
        logger.info(f"Nouvelle requête de chat: '{chat_request.message[:50]}...'")
        
        # Générer un ID de session si pas fourni
        session_id = chat_request.session_id or str(uuid.uuid4())
        
        # Convertir l'historique de conversation
        conversation_history = None
        if chat_request.conversation_history:
            conversation_history = [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in chat_request.conversation_history
            ]
        
        # Appeler le service RAG
        rag_response = await rag_service.generate_response(
            question=chat_request.message,
            conversation_history=conversation_history,
            include_web_search=chat_request.use_web_search,
            session_id=session_id
        )
        
        # Convertir les sources
        sources = []
        for source in rag_response.sources:
            sources.append(SourceInfo(
                chunk_id=source.chunk_id,
                filename=source.metadata.get('filename'),
                similarity=source.similarity,
                content_preview=source.content[:200] + "..." if len(source.content) > 200 else source.content
            ))
        
        # Convertir les résultats web
        web_results = []
        for web_result in rag_response.web_results:
            web_results.append(WebResultInfo(
                title=web_result.title,
                url=web_result.url,
                snippet=web_result.snippet
            ))
        
        # Créer la réponse
        response = ChatResponse(
            answer=rag_response.answer,
            sources=sources,
            web_results=web_results,
            confidence=rag_response.confidence,
            response_time=rag_response.response_time,
            session_id=session_id,
            metadata=rag_response.metadata
        )
        
        logger.info(f"Réponse générée pour session {session_id}")
        return response
        
    except Exception as e:
        logger.error(f"Erreur dans chat_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.post("/chat/stream")
async def chat_stream_endpoint(
    chat_request: StreamChatRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Endpoint de chat en streaming.
    
    Args:
        chat_request: Requête de chat pour streaming
        rag_service: Service RAG
        
    Returns:
        Stream de réponse
    """
    try:
        logger.info(f"Nouvelle requête de chat streaming: '{chat_request.message[:50]}...'")
        
        # Générer un ID de session
        session_id = chat_request.session_id or str(uuid.uuid4())
        
        # Convertir l'historique
        conversation_history = None
        if chat_request.conversation_history:
            conversation_history = [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in chat_request.conversation_history
            ]
        
        async def generate_stream():
            """Générateur pour le streaming."""
            try:
                # Obtenir la réponse en streaming
                async for chunk in rag_service.generate_response_stream(
                    question=chat_request.message,
                    conversation_history=conversation_history,
                    session_id=session_id
                ):
                    # Formater le chunk pour SSE
                    chunk_data = {
                        "content": chunk.get("content", ""),
                        "is_final": chunk.get("is_final", False),
                        "session_id": session_id,
                        "metadata": chunk.get("metadata")
                    }
                    
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Marquer la fin du stream
                final_chunk = {
                    "content": "",
                    "is_final": True,
                    "session_id": session_id,
                    "metadata": None
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                
            except Exception as e:
                logger.error(f"Erreur dans le streaming: {e}")
                error_chunk = {
                    "content": f"Erreur: {str(e)}",
                    "is_final": True,
                    "session_id": session_id,
                    "metadata": {"error": True}
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Erreur dans chat_stream_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/conversations/{session_id}")
async def get_conversation_history(
    session_id: str,
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Récupère l'historique d'une conversation.
    
    Args:
        session_id: ID de la session
        rag_service: Service RAG
        
    Returns:
        Historique de conversation
    """
    try:
        history = await rag_service.get_conversation_history(session_id)
        return {
            "session_id": session_id,
            "messages": history,
            "message_count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.delete("/conversations/{session_id}")
async def clear_conversation_history(
    session_id: str,
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Efface l'historique d'une conversation.
    
    Args:
        session_id: ID de la session
        rag_service: Service RAG
        
    Returns:
        Confirmation de suppression
    """
    try:
        await rag_service.clear_conversation_history(session_id)
        return {
            "message": f"Historique de la session {session_id} effacé",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'effacement de l'historique: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/search")
async def search_documents(
    query: str,
    top_k: int = 5,
    threshold: float = 0.7,
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Recherche dans la base de documents.
    
    Args:
        query: Requête de recherche
        top_k: Nombre de résultats
        threshold: Seuil de similarité
        rag_service: Service RAG
        
    Returns:
        Résultats de recherche
    """
    try:
        results = await rag_service.search_documents(
            query=query,
            top_k=top_k,
            threshold=threshold
        )
        
        return {
            "query": query,
            "results_count": len(results),
            "results": [
                {
                    "chunk_id": result.chunk_id,
                    "content": result.content[:300] + "..." if len(result.content) > 300 else result.content,
                    "similarity": result.similarity,
                    "metadata": result.metadata
                }
                for result in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/suggestions")
async def get_suggestions(
    partial_query: str,
    limit: int = 5,
    rag_service: RAGService = Depends(get_rag_service)
) -> Dict[str, Any]:
    """
    Obtient des suggestions de questions.
    
    Args:
        partial_query: Début de requête
        limit: Nombre de suggestions
        rag_service: Service RAG
        
    Returns:
        Suggestions de questions
    """
    try:
        suggestions = await rag_service.get_query_suggestions(
            partial_query=partial_query,
            limit=limit
        )
        
        return {
            "partial_query": partial_query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération de suggestions: {e}")
        # Retourner des suggestions par défaut en cas d'erreur
        return {
            "partial_query": partial_query,
            "suggestions": []
        } 