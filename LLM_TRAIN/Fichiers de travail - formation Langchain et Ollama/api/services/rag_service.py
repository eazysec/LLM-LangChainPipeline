"""
Service principal pour orchestrer le système RAG.
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime, timedelta
import uuid
import yaml

from ...embeddings.embedding_model import EmbeddingModel, create_embedding_model
from ...embeddings.build_index import VectorIndexBuilder, create_vector_index
from ...retriever.retriever import DocumentRetriever, create_retriever
from ...llm.ollama_client import OllamaClient, create_ollama_client
from ...llm.web_search import WebSearchClient, create_web_search_client
from ...llm.chain_builder import RAGChainBuilder, create_rag_chain, RAGResponse
from ...ingestion.loaders import DocumentLoader
from ...ingestion.preprocess import DocumentPreprocessor
from ...ingestion.chunking import DocumentChunker

logger = logging.getLogger(__name__)


class RAGService:
    """Service principal pour orchestrer le système RAG."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le service RAG.
        
        Args:
            config: Configuration du système
        """
        self.config = config
        self.start_time = time.time()
        
        # Composants du système RAG
        self.embedding_model: Optional[EmbeddingModel] = None
        self.vector_index: Optional[VectorIndexBuilder] = None
        self.retriever: Optional[DocumentRetriever] = None
        self.llm_client: Optional[OllamaClient] = None
        self.web_search_client: Optional[WebSearchClient] = None
        self.rag_chain: Optional[RAGChainBuilder] = None
        
        # Composants d'ingestion
        self.document_loader: Optional[DocumentLoader] = None
        self.document_preprocessor: Optional[DocumentPreprocessor] = None
        self.document_chunker: Optional[DocumentChunker] = None
        
        # Stockage des conversations
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.conversation_timestamps: Dict[str, datetime] = {}
        
        # Métriques
        self.metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_response_time': 0.0,
            'web_searches_performed': 0,
            'last_query_time': None
        }
        
        logger.info("Service RAG initialisé")
    
    async def initialize(self):
        """Initialise tous les composants du système RAG."""
        try:
            logger.info("Initialisation des composants RAG...")
            
            # 1. Modèle d'embeddings
            embedding_config = self.config.get('models', {}).get('embeddings', {})
            self.embedding_model = create_embedding_model(embedding_config)
            logger.info("Modèle d'embeddings initialisé")
            
            # 2. Index vectoriel
            db_config = self.config.get('database', {}).get('chroma', {})
            db_config['type'] = 'chroma'  # Forcer ChromaDB pour l'instant
            self.vector_index = create_vector_index(db_config)
            self.vector_index.set_embedding_model(self.embedding_model)
            logger.info("Index vectoriel initialisé")
            
            # 3. Récupérateur de documents
            retriever_config = self.config.get('rag', {})
            self.retriever = create_retriever(
                self.embedding_model,
                self.vector_index,
                retriever_config
            )
            logger.info("Récupérateur de documents initialisé")
            
            # 4. Client LLM (Ollama)
            llm_config = self.config.get('models', {}).get('ollama', {})
            self.llm_client = create_ollama_client(llm_config)
            logger.info("Client LLM initialisé")
            
            # 5. Client de recherche web
            web_config = self.config.get('web_search', {})
            if web_config.get('enabled', True):
                self.web_search_client = create_web_search_client(web_config)
                logger.info("Client de recherche web initialisé")
            
            # 6. Chaîne RAG
            rag_config = self.config.get('rag', {})
            self.rag_chain = create_rag_chain(
                self.llm_client,
                self.retriever,
                self.web_search_client,
                rag_config
            )
            logger.info("Chaîne RAG initialisée")
            
            # 7. Composants d'ingestion
            self.document_loader = DocumentLoader()
            self.document_preprocessor = DocumentPreprocessor()
            chunking_config = self.config.get('rag', {})
            self.document_chunker = DocumentChunker(
                chunk_size=chunking_config.get('chunk_size', 500),
                chunk_overlap=chunking_config.get('chunk_overlap', 50)
            )
            logger.info("Composants d'ingestion initialisés")
            
            logger.info("Tous les composants RAG initialisés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation: {e}")
            raise
    
    async def generate_response(self,
                              question: str,
                              conversation_history: Optional[List[Dict[str, str]]] = None,
                              include_web_search: Optional[bool] = None,
                              session_id: Optional[str] = None) -> RAGResponse:
        """
        Génère une réponse à une question.
        
        Args:
            question: Question de l'utilisateur
            conversation_history: Historique de conversation
            include_web_search: Forcer/empêcher la recherche web
            session_id: ID de session
            
        Returns:
            Réponse RAG complète
        """
        start_time = time.time()
        session_id = session_id or str(uuid.uuid4())
        
        try:
            # Mettre à jour les métriques
            self.metrics['total_queries'] += 1
            self.metrics['last_query_time'] = datetime.now()
            
            # Ajouter à l'historique de conversation
            self._add_to_conversation(session_id, "user", question)
            
            # Générer la réponse avec la chaîne RAG
            response = self.rag_chain.generate_response(
                question=question,
                conversation_history=conversation_history,
                include_web_search=include_web_search
            )
            
            # Ajouter la réponse à l'historique
            self._add_to_conversation(session_id, "assistant", response.answer)
            
            # Nettoyer les conversations anciennes
            self._cleanup_old_conversations()
            
            # Mettre à jour les métriques
            self.metrics['successful_queries'] += 1
            self.metrics['total_response_time'] += response.response_time
            
            if response.web_results:
                self.metrics['web_searches_performed'] += 1
            
            logger.info(f"Réponse générée pour session {session_id}")
            return response
            
        except Exception as e:
            self.metrics['failed_queries'] += 1
            logger.error(f"Erreur lors de la génération de réponse: {e}")
            
            # Créer une réponse d'erreur
            error_response = RAGResponse(
                answer=f"Désolé, une erreur s'est produite: {str(e)}",
                sources=[],
                web_results=[],
                confidence=0.0,
                response_time=time.time() - start_time,
                metadata={"error": True, "error_message": str(e)}
            )
            
            return error_response
    
    async def generate_response_stream(self,
                                     question: str,
                                     conversation_history: Optional[List[Dict[str, str]]] = None,
                                     session_id: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Génère une réponse en streaming.
        
        Args:
            question: Question de l'utilisateur
            conversation_history: Historique de conversation
            session_id: ID de session
            
        Yields:
            Chunks de réponse
        """
        session_id = session_id or str(uuid.uuid4())
        
        try:
            # Pour l'instant, simuler le streaming avec la réponse complète
            # TODO: Implémenter le vrai streaming avec Ollama
            response = await self.generate_response(
                question=question,
                conversation_history=conversation_history,
                session_id=session_id
            )
            
            # Diviser la réponse en chunks
            words = response.answer.split()
            chunk_size = 5  # Mots par chunk
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                chunk_content = " ".join(chunk_words)
                
                if i + chunk_size < len(words):
                    chunk_content += " "
                
                yield {
                    "content": chunk_content,
                    "is_final": False,
                    "session_id": session_id
                }
                
                # Petit délai pour simuler le streaming
                await asyncio.sleep(0.1)
            
            # Chunk final avec métadonnées
            yield {
                "content": "",
                "is_final": True,
                "session_id": session_id,
                "metadata": {
                    "sources": [
                        {
                            "chunk_id": source.chunk_id,
                            "filename": source.metadata.get('filename'),
                            "similarity": source.similarity
                        }
                        for source in response.sources
                    ],
                    "confidence": response.confidence,
                    "response_time": response.response_time
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du streaming: {e}")
            yield {
                "content": f"Erreur: {str(e)}",
                "is_final": True,
                "session_id": session_id,
                "metadata": {"error": True}
            }
    
    async def search_documents(self,
                             query: str,
                             top_k: int = 5,
                             threshold: float = 0.7) -> List[Any]:
        """
        Recherche dans les documents indexés.
        
        Args:
            query: Requête de recherche
            top_k: Nombre de résultats
            threshold: Seuil de similarité
            
        Returns:
            Résultats de recherche
        """
        try:
            results = self.retriever.retrieve(
                query=query,
                top_k=top_k,
                threshold=threshold
            )
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return []
    
    async def add_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ajoute un document à la base de connaissances.
        
        Args:
            file_path: Chemin vers le fichier
            metadata: Métadonnées additionnelles
            
        Returns:
            Résultat du traitement
        """
        try:
            start_time = time.time()
            
            # 1. Charger le document
            document = self.document_loader.load_document(file_path, metadata)
            
            # 2. Prétraiter
            processed_doc = self.document_preprocessor.preprocess_document(document)
            
            # 3. Découper en chunks
            chunks = self.document_chunker.chunk_document(processed_doc)
            
            # 4. Ajouter à l'index vectoriel
            chunks_added = self.vector_index.add_chunks(chunks)
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "message": "Document ajouté avec succès",
                "document_id": str(uuid.uuid4()),
                "chunks_created": chunks_added,
                "processing_time": processing_time,
                "document_info": processed_doc.get('metadata', {})
            }
            
            logger.info(f"Document ajouté: {file_path} - {chunks_added} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du document: {e}")
            return {
                "success": False,
                "message": f"Erreur: {str(e)}",
                "document_id": None,
                "chunks_created": 0,
                "processing_time": 0.0
            }
    
    async def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Récupère l'historique d'une conversation."""
        return self.conversations.get(session_id, [])
    
    async def clear_conversation_history(self, session_id: str):
        """Efface l'historique d'une conversation."""
        if session_id in self.conversations:
            del self.conversations[session_id]
        if session_id in self.conversation_timestamps:
            del self.conversation_timestamps[session_id]
    
    async def get_query_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """
        Génère des suggestions de requêtes.
        
        Args:
            partial_query: Début de requête
            limit: Nombre de suggestions
            
        Returns:
            Liste de suggestions
        """
        # Pour l'instant, retourner des suggestions statiques
        # TODO: Implémenter des suggestions intelligentes basées sur l'historique
        suggestions = [
            f"{partial_query} comment faire?",
            f"{partial_query} guide complet",
            f"{partial_query} étapes détaillées",
            f"{partial_query} exemples pratiques",
            f"{partial_query} bonnes pratiques"
        ]
        
        return suggestions[:limit]
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du système."""
        try:
            health_status = {
                "overall_status": "healthy",
                "components": {
                    "llm": self.llm_client.health_check() if self.llm_client else False,
                    "embedding_model": self.embedding_model is not None,
                    "vector_index": self.vector_index is not None,
                    "retriever": self.retriever is not None,
                    "web_search": self.web_search_client is not None
                },
                "metrics": self.get_metrics(),
                "uptime": time.time() - self.start_time
            }
            
            # Déterminer le statut global
            if not all(health_status["components"].values()):
                health_status["overall_status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Erreur lors du health check: {e}")
            return {
                "overall_status": "unhealthy",
                "error": str(e)
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques du système."""
        uptime_hours = (time.time() - self.start_time) / 3600
        
        return {
            "total_queries": self.metrics['total_queries'],
            "successful_queries": self.metrics['successful_queries'],
            "failed_queries": self.metrics['failed_queries'],
            "success_rate": (
                self.metrics['successful_queries'] / max(self.metrics['total_queries'], 1) * 100
            ),
            "average_response_time": (
                self.metrics['total_response_time'] / max(self.metrics['successful_queries'], 1)
            ),
            "queries_per_hour": self.metrics['total_queries'] / max(uptime_hours, 1/3600),
            "web_search_usage": (
                self.metrics['web_searches_performed'] / max(self.metrics['total_queries'], 1) * 100
            ),
            "active_conversations": len(self.conversations),
            "last_query_time": self.metrics['last_query_time']
        }
    
    def _add_to_conversation(self, session_id: str, role: str, content: str):
        """Ajoute un message à l'historique de conversation."""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversations[session_id].append(message)
        self.conversation_timestamps[session_id] = datetime.now()
        
        # Limiter la taille de l'historique
        max_history = self.config.get('database', {}).get('conversations', {}).get('max_history', 10)
        if len(self.conversations[session_id]) > max_history * 2:  # user + assistant
            self.conversations[session_id] = self.conversations[session_id][-max_history * 2:]
    
    def _cleanup_old_conversations(self):
        """Nettoie les conversations anciennes."""
        try:
            timeout = self.config.get('database', {}).get('conversations', {}).get('session_timeout', 3600)
            cutoff_time = datetime.now() - timedelta(seconds=timeout)
            
            sessions_to_remove = []
            for session_id, timestamp in self.conversation_timestamps.items():
                if timestamp < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.conversations[session_id]
                del self.conversation_timestamps[session_id]
            
            if sessions_to_remove:
                logger.info(f"Nettoyage: {len(sessions_to_remove)} conversations supprimées")
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des conversations: {e}")
    
    async def cleanup(self):
        """Nettoie les ressources."""
        try:
            logger.info("Nettoyage des ressources du service RAG...")
            
            # Sauvegarder les métriques si nécessaire
            # TODO: Implémenter la persistance des métriques
            
            # Fermer les connexions
            if self.llm_client:
                pass  # Pas de cleanup spécifique pour Ollama
            
            logger.info("Nettoyage terminé")
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}") 