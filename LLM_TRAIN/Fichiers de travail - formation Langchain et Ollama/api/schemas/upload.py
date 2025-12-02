"""
Schémas Pydantic pour l'upload de documents.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentInfo(BaseModel):
    """Informations sur un document."""
    filename: str = Field(..., description="Nom du fichier")
    size: int = Field(..., description="Taille en bytes")
    extension: str = Field(..., description="Extension du fichier")
    mime_type: Optional[str] = Field(default=None, description="Type MIME")
    uploaded_at: datetime = Field(..., description="Date d'upload")
    processed: bool = Field(default=False, description="Indique si le document est traité")
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "guide_installation.pdf",
                "size": 1024000,
                "extension": ".pdf",
                "mime_type": "application/pdf",
                "uploaded_at": "2024-01-01T10:00:00Z",
                "processed": True
            }
        }


class UploadResponse(BaseModel):
    """Réponse après upload d'un document."""
    success: bool = Field(..., description="Indique si l'upload a réussi")
    message: str = Field(..., description="Message de statut")
    document_id: Optional[str] = Field(default=None, description="ID du document uploadé")
    document_info: Optional[DocumentInfo] = Field(default=None, description="Infos du document")
    chunks_created: int = Field(default=0, description="Nombre de chunks créés")
    processing_time: float = Field(default=0.0, description="Temps de traitement")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Document uploadé et traité avec succès",
                "document_id": "doc_123",
                "document_info": {
                    "filename": "guide.pdf",
                    "size": 1024000,
                    "extension": ".pdf",
                    "mime_type": "application/pdf",
                    "uploaded_at": "2024-01-01T10:00:00Z",
                    "processed": True
                },
                "chunks_created": 25,
                "processing_time": 3.5
            }
        }


class BulkUploadResponse(BaseModel):
    """Réponse pour l'upload en lot."""
    total_files: int = Field(..., description="Nombre total de fichiers")
    successful_uploads: int = Field(..., description="Nombre d'uploads réussis")
    failed_uploads: int = Field(..., description="Nombre d'uploads échoués")
    results: List[UploadResponse] = Field(..., description="Résultats détaillés")
    total_processing_time: float = Field(..., description="Temps total de traitement")
    
    class Config:
        schema_extra = {
            "example": {
                "total_files": 3,
                "successful_uploads": 2,
                "failed_uploads": 1,
                "results": [
                    {
                        "success": True,
                        "message": "Traitement réussi",
                        "document_id": "doc_1",
                        "chunks_created": 10
                    }
                ],
                "total_processing_time": 15.2
            }
        }


class ProcessingStatus(BaseModel):
    """Statut de traitement d'un document."""
    document_id: str = Field(..., description="ID du document")
    status: str = Field(..., description="Statut (pending/processing/completed/failed)")
    progress: float = Field(default=0.0, description="Progression (0-100)")
    message: Optional[str] = Field(default=None, description="Message de statut")
    started_at: datetime = Field(..., description="Heure de début")
    completed_at: Optional[datetime] = Field(default=None, description="Heure de fin")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "doc_123",
                "status": "completed",
                "progress": 100.0,
                "message": "Document traité avec succès",
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:00:30Z"
            }
        } 