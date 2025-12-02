"""
Routes pour l'upload de documents.
"""

import logging
import os
import tempfile
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import JSONResponse

from ..services.rag_service import RAGService
from ..schemas.upload import UploadResponse, BulkUploadResponse, DocumentInfo, ProcessingStatus

logger = logging.getLogger(__name__)

router = APIRouter()


def get_rag_service() -> RAGService:
    """Dependency pour obtenir le service RAG."""
    from ..main import rag_service
    return rag_service


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    description: str = Form(None),
    tags: str = Form(None),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Upload un document et l'ajoute à la base de connaissances.
    
    Args:
        file: Fichier à uploader
        description: Description optionnelle
        tags: Tags séparés par des virgules
        rag_service: Service RAG
        
    Returns:
        Résultat de l'upload
    """
    try:
        # Vérifier le type de fichier
        allowed_extensions = {'.pdf', '.txt', '.md', '.docx'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Type de fichier non supporté. Extensions autorisées: {', '.join(allowed_extensions)}"
            )
        
        # Vérifier la taille du fichier (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail="Fichier trop volumineux (max 50MB)"
            )
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Préparer les métadonnées
            metadata = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content),
                "description": description,
                "tags": tags.split(',') if tags else []
            }
            
            # Ajouter le document
            result = await rag_service.add_document(temp_file_path, metadata)
            
            if result["success"]:
                return UploadResponse(
                    success=True,
                    message="Document ajouté avec succès",
                    document_info=DocumentInfo(
                        filename=file.filename,
                        file_size=len(content),
                        content_type=file.content_type,
                        chunks_created=result["chunks_created"],
                        processing_time=result["processing_time"]
                    )
                )
            else:
                raise HTTPException(status_code=500, detail=result["message"])
                
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.post("/upload/bulk", response_model=BulkUploadResponse)
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Upload plusieurs documents en une fois.
    
    Args:
        files: Liste des fichiers à uploader
        rag_service: Service RAG
        
    Returns:
        Résultat du bulk upload
    """
    try:
        results = []
        successful_uploads = 0
        failed_uploads = 0
        
        for file in files:
            try:
                # Utiliser la même logique que l'upload simple
                allowed_extensions = {'.pdf', '.txt', '.md', '.docx'}
                file_extension = os.path.splitext(file.filename)[1].lower()
                
                if file_extension not in allowed_extensions:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "message": f"Type de fichier non supporté: {file_extension}"
                    })
                    failed_uploads += 1
                    continue
                
                content = await file.read()
                max_size = 50 * 1024 * 1024  # 50MB
                if len(content) > max_size:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "message": "Fichier trop volumineux (max 50MB)"
                    })
                    failed_uploads += 1
                    continue
                
                # Créer un fichier temporaire
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                
                try:
                    metadata = {
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "size": len(content)
                    }
                    
                    result = await rag_service.add_document(temp_file_path, metadata)
                    
                    if result["success"]:
                        results.append({
                            "filename": file.filename,
                            "success": True,
                            "message": "Document ajouté avec succès",
                            "chunks_created": result["chunks_created"]
                        })
                        successful_uploads += 1
                    else:
                        results.append({
                            "filename": file.filename,
                            "success": False,
                            "message": result["message"]
                        })
                        failed_uploads += 1
                        
                finally:
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "message": f"Erreur: {str(e)}"
                })
                failed_uploads += 1
        
        return BulkUploadResponse(
            total_files=len(files),
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du bulk upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/upload/status/{document_id}")
async def get_upload_status(document_id: str):
    """
    Récupère le statut de traitement d'un document.
    
    Args:
        document_id: ID du document
        
    Returns:
        Statut du traitement
    """
    # Pour l'instant, retourner un statut simulé
    # TODO: Implémenter un vrai système de suivi des uploads
    return ProcessingStatus(
        document_id=document_id,
        status="completed",
        progress=100,
        message="Document traité avec succès",
        chunks_created=15,
        processing_time=2.5
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Supprime un document de la base de connaissances.
    
    Args:
        document_id: ID du document à supprimer
        rag_service: Service RAG
        
    Returns:
        Confirmation de suppression
    """
    try:
        # TODO: Implémenter la suppression de documents
        # Pour l'instant, retourner une réponse simulée
        return JSONResponse({
            "success": True,
            "message": f"Document {document_id} supprimé avec succès"
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.get("/documents")
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Liste les documents dans la base de connaissances.
    
    Args:
        limit: Nombre de documents à retourner
        offset: Décalage pour la pagination
        rag_service: Service RAG
        
    Returns:
        Liste des documents
    """
    try:
        # TODO: Implémenter la récupération de la liste des documents
        # Pour l'instant, retourner une liste simulée
        documents = [
            {
                "document_id": f"doc_{i}",
                "filename": f"document_{i}.pdf",
                "upload_date": "2024-01-01T10:00:00",
                "size": 1024 * (i + 1),
                "chunks_count": 10 + i,
                "status": "indexed"
            }
            for i in range(offset, min(offset + limit, 20))
        ]
        
        return {
            "documents": documents,
            "total": 20,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}") 