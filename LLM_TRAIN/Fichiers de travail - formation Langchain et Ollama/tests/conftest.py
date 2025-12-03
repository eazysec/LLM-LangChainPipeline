"""
Configuration des tests pytest.
"""

import pytest
import tempfile
import os
import shutil
from typing import Dict, Any
from unittest.mock import MagicMock

# Imports conditionnels pour éviter les erreurs lors des tests
try:
    from ingestion.loaders import DocumentLoader
    from ingestion.preprocess import DocumentPreprocessor
    from ingestion.chunking import DocumentChunker
except ImportError:
    DocumentLoader = type('DocumentLoader', (), {})
    DocumentPreprocessor = type('DocumentPreprocessor', (), {})
    DocumentChunker = type('DocumentChunker', (), {})

try:
    from embeddings.embedding_model import EmbeddingModel
    from embeddings.build_index import VectorIndexBuilder
except ImportError:
    EmbeddingModel = type('EmbeddingModel', (), {})
    VectorIndexBuilder = type('VectorIndexBuilder', (), {})

try:
    from retriever.retriever import DocumentRetriever
except ImportError:
    DocumentRetriever = type('DocumentRetriever', (), {})

try:
    from llm.ollama_client import OllamaClient
    from llm.web_search import WebSearchClient
except ImportError:
    OllamaClient = type('OllamaClient', (), {})
    WebSearchClient = type('WebSearchClient', (), {})

try:
    from api.services.rag_service import RAGService
except ImportError:
    RAGService = type('RAGService', (), {})


@pytest.fixture
def test_config():
    """Configuration de test."""
    return {
        'app': {
            'name': 'test-chatbot-rag',
            'host': '0.0.0.0',
            'port': 8000,
            'debug': True
        },
        'models': {
            'ollama': {
                'base_url': 'http://100.64.0.34:11434',
                'model_name': 'qwen2.5:latest',
                'temperature': 0.7,
                'max_tokens': 2048,
                'timeout': 30
            },
            'embeddings': {
                'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
                'device': 'cpu',
                'cache_folder': '.embeddings_cache'
            }
        },
        'database': {
            'chroma': {
                'persist_directory': './data/chroma_test',
                'collection_name': 'test_documents'
            },
            'conversations': {
                'max_history': 10,
                'session_timeout': 3600
            }
        },
        'rag': {
            'chunk_size': 500,
            'chunk_overlap': 50,
            'top_k': 5,
            'similarity_threshold': 0.7,
            'enable_reranking': True,
            'web_search_fallback': True
        },
        'web_search': {
            'enabled': True,
            'engine': 'duckduckgo',
            'max_results': 5,
            'timeout': 10
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }


@pytest.fixture
def temp_dir():
    """Répertoire temporaire pour les tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_text():
    """Texte d'exemple pour les tests."""
    return """
    Intelligence artificielle et apprentissage automatique

    L'intelligence artificielle (IA) est une technologie qui permet aux machines 
    de simuler l'intelligence humaine. L'apprentissage automatique est une 
    sous-catégorie de l'IA qui permet aux systèmes d'apprendre automatiquement 
    à partir de données sans être explicitement programmés.

    Les réseaux de neurones artificiels sont inspirés du fonctionnement du 
    cerveau humain. Ils sont composés de nœuds interconnectés qui traitent 
    l'information de manière parallèle.

    Applications de l'IA:
    - Reconnaissance vocale
    - Vision par ordinateur  
    - Traitement du langage naturel
    - Véhicules autonomes
    - Diagnostic médical
    """


@pytest.fixture
def sample_pdf_content():
    """Contenu PDF simulé."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"


@pytest.fixture
def mock_embedding_model():
    """Mock du modèle d'embeddings."""
    mock = MagicMock(spec=EmbeddingModel)
    mock.encode.return_value = [[0.1, 0.2, 0.3, 0.4] for _ in range(5)]
    mock.get_dimension.return_value = 4
    mock.similarity.return_value = 0.8
    return mock


@pytest.fixture
def mock_ollama_client():
    """Mock du client Ollama."""
    mock = MagicMock(spec=OllamaClient)
    mock.generate.return_value = "Réponse générée par le modèle de test"
    mock.generate_async.return_value = "Réponse async générée par le modèle de test"
    mock.health_check.return_value = True
    return mock


@pytest.fixture
def mock_web_search_client():
    """Mock du client de recherche web."""
    mock = MagicMock(spec=WebSearchClient)
    mock.search.return_value = [
        {
            'title': 'Résultat de test 1',
            'snippet': 'Description du résultat 1',
            'url': 'https://example.com/1',
            'relevance': 0.9
        },
        {
            'title': 'Résultat de test 2', 
            'snippet': 'Description du résultat 2',
            'url': 'https://example.com/2',
            'relevance': 0.8
        }
    ]
    return mock


@pytest.fixture
def document_loader():
    """Instance du chargeur de documents."""
    return DocumentLoader()


@pytest.fixture
def document_preprocessor():
    """Instance du préprocesseur de documents."""
    return DocumentPreprocessor()


@pytest.fixture
def document_chunker():
    """Instance du découpage de documents."""
    return DocumentChunker(chunk_size=100, chunk_overlap=20)


@pytest.fixture
def mock_vector_index():
    """Mock de l'index vectoriel."""
    mock = MagicMock(spec=VectorIndexBuilder)
    mock.add_chunks.return_value = 5
    mock.search.return_value = [
        {
            'chunk_id': 'chunk_1',
            'content': 'Contenu du chunk 1',
            'metadata': {'filename': 'test.txt'},
            'similarity': 0.9
        },
        {
            'chunk_id': 'chunk_2',
            'content': 'Contenu du chunk 2', 
            'metadata': {'filename': 'test.txt'},
            'similarity': 0.8
        }
    ]
    return mock


@pytest.fixture
def mock_rag_service(test_config, mock_embedding_model, mock_ollama_client, mock_web_search_client):
    """Mock du service RAG."""
    service = RAGService(test_config)
    service.embedding_model = mock_embedding_model
    service.llm_client = mock_ollama_client
    service.web_search_client = mock_web_search_client
    return service


@pytest.fixture
def test_document_metadata():
    """Métadonnées de test pour un document."""
    return {
        'filename': 'test_document.pdf',
        'content_type': 'application/pdf',
        'size': 1024,
        'upload_date': '2024-01-15T10:00:00',
        'tags': ['test', 'IA', 'machine learning']
    }


@pytest.fixture
def sample_conversation_history():
    """Historique de conversation d'exemple."""
    return [
        {'role': 'user', 'content': 'Qu\'est-ce que l\'intelligence artificielle?'},
        {'role': 'assistant', 'content': 'L\'IA est une technologie...'},
        {'role': 'user', 'content': 'Comment fonctionne l\'apprentissage automatique?'},
        {'role': 'assistant', 'content': 'L\'apprentissage automatique utilise...'}
    ]


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Configure les logs pour les tests."""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    # Désactiver les logs trop verbeux pendant les tests
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING) 