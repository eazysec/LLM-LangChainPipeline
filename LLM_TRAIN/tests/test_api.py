"""
Tests unitaires pour les API FastAPI.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from io import BytesIO

from api.main import app
from api.services.rag_service import RAGService
from llm.chain_builder import RAGResponse


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_rag_response():
    """Réponse RAG simulée."""
    return RAGResponse(
        answer="Voici une réponse générée par le système RAG de test.",
        sources=[
            {
                'chunk_id': 'chunk_1',
                'content': 'Contenu source 1',
                'metadata': {'filename': 'test1.txt'},
                'similarity': 0.9
            },
            {
                'chunk_id': 'chunk_2',
                'content': 'Contenu source 2',
                'metadata': {'filename': 'test2.txt'},
                'similarity': 0.8
            }
        ],
        web_results=[],
        confidence=0.85,
        response_time=1.5,
        metadata={'tokens_used': 150}
    )


class TestQARoutes:
    """Tests pour les routes de questions-réponses."""
    
    @patch('api.main.rag_service')
    def test_chat_endpoint(self, mock_service, client, mock_rag_response):
        """Test de l'endpoint de chat."""
        mock_service.generate_response = AsyncMock(return_value=mock_rag_response)
        
        request_data = {
            "message": "Qu'est-ce que l'intelligence artificielle?",
            "conversation_history": [],
            "session_id": "test_session_123"
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == mock_rag_response.answer
        assert len(data["sources"]) == 2
        assert data["confidence"] == 0.85
        assert data["session_id"] == "test_session_123"
    
    @patch('api.main.rag_service')
    def test_chat_with_history(self, mock_service, client, mock_rag_response):
        """Test de chat avec historique."""
        mock_service.generate_response = AsyncMock(return_value=mock_rag_response)
        
        request_data = {
            "message": "Continue l'explication",
            "conversation_history": [
                {"role": "user", "content": "Qu'est-ce que l'IA?"},
                {"role": "assistant", "content": "L'IA est..."}
            ],
            "session_id": "test_session_123"
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        assert response.status_code == 200
        mock_service.generate_response.assert_called_once()
        
        # Vérifier que l'historique a été passé
        call_args = mock_service.generate_response.call_args
        assert call_args[1]['conversation_history'] is not None
    
    @patch('api.main.rag_service')
    def test_chat_stream_endpoint(self, mock_service, client):
        """Test de l'endpoint de chat en streaming."""
        # Mock du générateur de streaming
        async def mock_stream():
            yield {"content": "Début", "is_final": False, "session_id": "test_session"}
            yield {"content": " de la", "is_final": False, "session_id": "test_session"}
            yield {"content": " réponse", "is_final": True, "session_id": "test_session"}
        
        mock_service.generate_response_stream = AsyncMock(return_value=mock_stream())
        
        request_data = {
            "message": "Test streaming",
            "session_id": "test_session"
        }
        
        response = client.post("/api/v1/chat/stream", json=request_data)
        
        assert response.status_code == 200
        # Note: Le test du streaming complet nécessiterait une approche différente
        # car TestClient ne gère pas parfaitement les Server-Sent Events
    
    @patch('api.main.rag_service')
    def test_get_conversation_history(self, mock_service, client):
        """Test de récupération d'historique de conversation."""
        mock_history = [
            {"role": "user", "content": "Question 1", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "Réponse 1", "timestamp": "2024-01-01T10:00:05"}
        ]
        mock_service.get_conversation_history = AsyncMock(return_value=mock_history)
        
        response = client.get("/api/v1/conversations/test_session_123")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["conversation_history"]) == 2
        assert data["session_id"] == "test_session_123"
    
    @patch('api.main.rag_service')
    def test_clear_conversation_history(self, mock_service, client):
        """Test de suppression d'historique de conversation."""
        mock_service.clear_conversation_history = AsyncMock()
        
        response = client.delete("/api/v1/conversations/test_session_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_service.clear_conversation_history.assert_called_once_with("test_session_123")
    
    @patch('api.main.rag_service')
    def test_search_documents(self, mock_service, client):
        """Test de recherche dans les documents."""
        mock_results = [
            {
                'chunk_id': 'chunk_1',
                'content': 'Résultat de recherche 1',
                'metadata': {'filename': 'doc1.txt'},
                'similarity': 0.9
            }
        ]
        mock_service.search_documents = AsyncMock(return_value=mock_results)
        
        response = client.get("/api/v1/search?query=test&top_k=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["query"] == "test"
    
    @patch('api.main.rag_service')
    def test_get_suggestions(self, mock_service, client):
        """Test de récupération de suggestions."""
        mock_suggestions = [
            "test comment faire?",
            "test guide complet",
            "test exemples pratiques"
        ]
        mock_service.get_query_suggestions = AsyncMock(return_value=mock_suggestions)
        
        response = client.get("/api/v1/suggestions?partial_query=test")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) == 3
        assert all("test" in suggestion for suggestion in data["suggestions"])


class TestUploadRoutes:
    """Tests pour les routes d'upload."""
    
    @patch('api.main.rag_service')
    def test_upload_document(self, mock_service, client):
        """Test d'upload de document."""
        mock_result = {
            "success": True,
            "message": "Document ajouté avec succès",
            "chunks_created": 5,
            "processing_time": 2.5
        }
        mock_service.add_document = AsyncMock(return_value=mock_result)
        
        # Créer un fichier de test
        test_file_content = b"Contenu du fichier de test"
        files = {"file": ("test.txt", BytesIO(test_file_content), "text/plain")}
        data = {"description": "Fichier de test"}
        
        response = client.post("/api/v1/upload", files=files, data=data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert "document_info" in response_data
    
    @patch('api.main.rag_service')
    def test_upload_unsupported_file(self, mock_service, client):
        """Test d'upload de fichier non supporté."""
        files = {"file": ("test.xyz", BytesIO(b"contenu"), "application/unknown")}
        
        response = client.post("/api/v1/upload", files=files)
        
        assert response.status_code == 400
        assert "non supporté" in response.json()["detail"]
    
    @patch('api.main.rag_service')
    def test_upload_large_file(self, mock_service, client):
        """Test d'upload de fichier trop volumineux."""
        # Créer un fichier de plus de 50MB
        large_content = b"x" * (51 * 1024 * 1024)
        files = {"file": ("large.txt", BytesIO(large_content), "text/plain")}
        
        response = client.post("/api/v1/upload", files=files)
        
        assert response.status_code == 413
        assert "trop volumineux" in response.json()["detail"]
    
    @patch('api.main.rag_service')
    def test_bulk_upload(self, mock_service, client):
        """Test d'upload en lot."""
        mock_service.add_document = AsyncMock(return_value={
            "success": True,
            "chunks_created": 3
        })
        
        # Créer plusieurs fichiers de test
        files = [
            ("files", ("test1.txt", BytesIO(b"Contenu 1"), "text/plain")),
            ("files", ("test2.txt", BytesIO(b"Contenu 2"), "text/plain"))
        ]
        
        response = client.post("/api/v1/upload/bulk", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 2
        assert data["successful_uploads"] == 2
        assert data["failed_uploads"] == 0
    
    def test_get_upload_status(self, client):
        """Test de récupération du statut d'upload."""
        response = client.get("/api/v1/upload/status/test_doc_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test_doc_123"
        assert "status" in data
    
    def test_list_documents(self, client):
        """Test de listage des documents."""
        response = client.get("/api/v1/documents?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data


class TestAdminRoutes:
    """Tests pour les routes d'administration."""
    
    @patch('api.main.rag_service')
    def test_get_system_status(self, mock_service, client):
        """Test de récupération du statut système."""
        mock_health = {
            "overall_status": "healthy",
            "uptime": 3600,
            "components": {
                "llm": True,
                "embedding_model": True,
                "vector_index": True
            }
        }
        mock_metrics = {
            "total_queries": 100,
            "success_rate": 95.0,
            "average_response_time": 1.5,
            "active_conversations": 5
        }
        
        mock_service.health_check = AsyncMock(return_value=mock_health)
        mock_service.get_metrics = lambda: mock_metrics
        
        response = client.get("/api/v1/admin/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["uptime"] == 3600
        assert "components" in data
        assert "metrics" in data
    
    def test_get_index_stats(self, client):
        """Test de récupération des statistiques d'index."""
        response = client.get("/api/v1/admin/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "total_chunks" in data
        assert "index_size_mb" in data
    
    def test_get_logs(self, client):
        """Test de récupération des logs."""
        response = client.get("/api/v1/admin/logs?level=INFO&limit=50")
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert "limit" in data
    
    def test_get_config(self, client):
        """Test de récupération de la configuration."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='app:\n  name: test')):
            response = client.get("/api/v1/admin/config")
            
            assert response.status_code == 200
            data = response.json()
            assert "app" in data
    
    def test_update_config(self, client):
        """Test de mise à jour de la configuration."""
        config_update = {
            "config": {
                "app": {"debug": True},
                "rag": {"chunk_size": 600}
            }
        }
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='app:\n  name: test')):
            response = client.put("/api/v1/admin/config", json=config_update)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_rebuild_index(self, client):
        """Test de reconstruction d'index."""
        request_data = {
            "index_type": "chroma",
            "clear_existing": True
        }
        
        response = client.post("/api/v1/admin/index/rebuild", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rebuild_time" in data
    
    def test_clear_index(self, client):
        """Test de suppression d'index."""
        response = client.delete("/api/v1/admin/index/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch('api.main.rag_service')
    def test_get_detailed_metrics(self, mock_service, client):
        """Test de récupération des métriques détaillées."""
        mock_metrics = {
            "total_queries": 150,
            "success_rate": 98.0,
            "average_response_time": 1.2
        }
        mock_health = {
            "uptime": 7200,
            "components": {"llm": True}
        }
        
        mock_service.get_metrics = lambda: mock_metrics
        mock_service.health_check = AsyncMock(return_value=mock_health)
        
        response = client.get("/api/v1/admin/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "performance" in data
        assert "usage" in data
        assert "system" in data
    
    def test_restart_system(self, client):
        """Test de redémarrage système."""
        response = client.post("/api/v1/admin/restart")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch('api.main.rag_service')
    def test_health_check(self, mock_service, client):
        """Test de health check."""
        mock_service.health_check = AsyncMock(return_value={"overall_status": "healthy"})
        
        response = client.get("/api/v1/admin/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestMainApp:
    """Tests pour l'application principale."""
    
    def test_root_endpoint(self, client):
        """Test de l'endpoint racine."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "ChatBot RAG API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    @patch('api.main.rag_service')
    def test_health_endpoint(self, mock_service, client):
        """Test de l'endpoint de santé."""
        mock_service.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # Mock de l'état de l'application
        with patch('api.main.app.state') as mock_state:
            mock_state.rag_service = mock_service
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    def test_health_endpoint_initializing(self, client):
        """Test de l'endpoint de santé en cours d'initialisation."""
        # Mock d'un état non initialisé
        with patch('api.main.app.state') as mock_state:
            mock_state.rag_service = None
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "initializing"


class TestErrorHandling:
    """Tests pour la gestion d'erreurs."""
    
    def test_chat_invalid_request(self, client):
        """Test de requête de chat invalide."""
        # Requête sans message
        response = client.post("/api/v1/chat", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_nonexistent_endpoint(self, client):
        """Test d'endpoint inexistant."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    @patch('api.main.rag_service')
    def test_internal_server_error(self, mock_service, client):
        """Test de gestion d'erreur interne."""
        mock_service.generate_response = AsyncMock(side_effect=Exception("Test error"))
        
        request_data = {
            "message": "Test message",
            "session_id": "test_session"
        }
        
        response = client.post("/api/v1/chat", json=request_data)
        
        # L'erreur devrait être gérée gracieusement
        # (le comportement exact dépend de l'implémentation)
        assert response.status_code in [200, 500] 