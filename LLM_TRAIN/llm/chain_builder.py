"""
Constructeur de chaînes RAG pour orchestrer la génération de réponses.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import time
from dataclasses import dataclass

from llm.ollama_client import OllamaClient
from llm.web_search import WebSearchClient, WebSearchResult
from retriever.retriever import DocumentRetriever, RetrievalResult

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Réponse complète du système RAG."""
    answer: str
    sources: List[RetrievalResult]
    web_results: List[WebSearchResult]
    confidence: float
    response_time: float
    metadata: Dict[str, Any]


class RAGChainBuilder:
    """Constructeur de chaînes RAG pour orchestrer la génération."""
    
    def __init__(self,
                 llm_client: OllamaClient,
                 retriever: DocumentRetriever,
                 web_search_client: Optional[WebSearchClient] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialise le constructeur de chaînes RAG.
        
        Args:
            llm_client: Client LLM pour la génération
            retriever: Récupérateur de documents
            web_search_client: Client de recherche web optionnel
            config: Configuration du système RAG
        """
        self.llm_client = llm_client
        self.retriever = retriever
        self.web_search_client = web_search_client
        self.config = config or {}
        
        # Configuration
        self.use_web_search = self.config.get('use_web_search', True)
        self.min_confidence_threshold = self.config.get('min_confidence', 0.5)
        self.max_context_chunks = self.config.get('max_context_chunks', 5)
        self.enable_reranking = self.config.get('enable_reranking', True)
        
        logger.info("Constructeur de chaînes RAG initialisé")
    
    def generate_response(self,
                         question: str,
                         conversation_history: Optional[List[Dict[str, str]]] = None,
                         include_web_search: Optional[bool] = None) -> RAGResponse:
        """
        Génère une réponse RAG complète.
        
        Args:
            question: Question de l'utilisateur
            conversation_history: Historique de conversation
            include_web_search: Forcer/empêcher la recherche web
            
        Returns:
            Réponse RAG complète
        """
        start_time = time.time()
        
        try:
            logger.info(f"Génération RAG pour: '{question[:50]}...'")
            
            # 1. Récupération des documents pertinents
            retrieval_results = self._retrieve_documents(question, conversation_history)
            
            # 2. Évaluation de la confiance
            confidence = self._calculate_confidence(retrieval_results, question)
            
            # 3. Décision de recherche web
            should_search_web = self._should_use_web_search(
                question, confidence, include_web_search
            )
            
            # 4. Recherche web si nécessaire
            web_results = []
            if should_search_web:
                web_results = self._perform_web_search(question)
            
            # 5. Construction du contexte
            context_chunks = self._build_context(retrieval_results, web_results)
            
            # 6. Génération de la réponse
            answer = self._generate_answer(question, context_chunks, conversation_history)
            
            # 7. Post-traitement
            answer = self._post_process_answer(answer, retrieval_results, web_results)
            
            response_time = time.time() - start_time
            
            # Créer la réponse finale
            rag_response = RAGResponse(
                answer=answer,
                sources=retrieval_results,
                web_results=web_results,
                confidence=confidence,
                response_time=response_time,
                metadata={
                    'context_chunks': len(context_chunks),
                    'web_search_used': should_search_web,
                    'model_name': self.llm_client.model_name,
                    'timestamp': time.time()
                }
            )
            
            logger.info(f"Réponse RAG générée en {response_time:.2f}s")
            return rag_response
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération RAG: {e}")
            
            # Réponse d'erreur
            return RAGResponse(
                answer=f"Désolé, une erreur s'est produite lors de la génération de la réponse: {str(e)}",
                sources=[],
                web_results=[],
                confidence=0.0,
                response_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    def _retrieve_documents(self,
                           question: str,
                           conversation_history: Optional[List[Dict[str, str]]]) -> List[RetrievalResult]:
        """Récupère les documents pertinents."""
        try:
            if conversation_history:
                # Récupération contextuelle
                results = self.retriever.retrieve_with_context(
                    question,
                    conversation_history,
                    top_k=self.max_context_chunks
                )
            else:
                # Récupération standard
                results = self.retriever.retrieve(
                    question,
                    top_k=self.max_context_chunks
                )
            
            logger.debug(f"Documents récupérés: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération: {e}")
            return []
    
    def _calculate_confidence(self,
                            retrieval_results: List[RetrievalResult],
                            question: str) -> float:
        """Calcule la confiance dans les résultats de récupération."""
        if not retrieval_results:
            return 0.0
        
        try:
            # Confiance basée sur la similarité moyenne
            similarities = [result.similarity for result in retrieval_results]
            avg_similarity = sum(similarities) / len(similarities)
            
            # Ajustements
            confidence = avg_similarity
            
            # Bonus si le premier résultat est très pertinent
            if retrieval_results[0].similarity > 0.8:
                confidence += 0.1
            
            # Bonus si plusieurs résultats sont pertinents
            high_sim_count = sum(1 for sim in similarities if sim > 0.7)
            if high_sim_count >= 2:
                confidence += 0.05
            
            # Limiter entre 0 et 1
            confidence = max(0.0, min(1.0, confidence))
            
            logger.debug(f"Confiance calculée: {confidence:.3f}")
            return confidence
            
        except Exception as e:
            logger.error(f"Erreur calcul confiance: {e}")
            return 0.0
    
    def _should_use_web_search(self,
                              question: str,
                              confidence: float,
                              force_web_search: Optional[bool]) -> bool:
        """Détermine si la recherche web doit être utilisée."""
        # Respect du paramètre forcé
        if force_web_search is not None:
            return force_web_search and self.web_search_client is not None
        
        # Pas de client de recherche web
        if not self.web_search_client or not self.use_web_search:
            return False
        
        # Utiliser la logique du client de recherche web
        return self.web_search_client.should_search_web(question, confidence)
    
    def _perform_web_search(self, question: str) -> List[WebSearchResult]:
        """Effectue une recherche web."""
        if not self.web_search_client:
            return []
        
        try:
            max_results = self.config.get('web_max_results', 3)
            results = self.web_search_client.search(question, max_results)
            logger.debug(f"Résultats web: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Erreur recherche web: {e}")
            return []
    
    def _build_context(self,
                      retrieval_results: List[RetrievalResult],
                      web_results: List[WebSearchResult]) -> List[str]:
        """Construit le contexte pour la génération."""
        context_chunks = []
        
        # Ajouter les résultats de récupération
        for result in retrieval_results:
            chunk_text = f"[Document: {result.metadata.get('filename', 'Unknown')}]\n"
            chunk_text += result.content
            context_chunks.append(chunk_text)
        
        # Ajouter les résultats web si disponibles
        if web_results:
            web_context = []
            for result in web_results:
                web_text = f"[Web: {result.title}]\n{result.snippet}"
                web_context.append(web_text)
            
            # Ajouter en tant que chunk séparé
            if web_context:
                web_chunk = "[INFORMATIONS WEB RÉCENTES]\n" + "\n\n".join(web_context)
                context_chunks.append(web_chunk)
        
        return context_chunks
    
    def _generate_answer(self,
                        question: str,
                        context_chunks: List[str],
                        conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """Génère la réponse avec le LLM."""
        try:
            # Construire le prompt RAG
            prompt = self.llm_client.build_rag_prompt(
                question, context_chunks, conversation_history
            )
            
            # Générer la réponse
            answer = self.llm_client.generate(prompt)
            
            return answer
            
        except Exception as e:
            logger.error(f"Erreur génération réponse: {e}")
            return f"Désolé, je n'ai pas pu générer une réponse appropriée. Erreur: {str(e)}"
    
    def _post_process_answer(self,
                           answer: str,
                           retrieval_results: List[RetrievalResult],
                           web_results: List[WebSearchResult]) -> str:
        """Post-traite la réponse générée."""
        try:
            # Nettoyer la réponse
            processed_answer = answer.strip()
            
            # Ajouter des références si configuré
            if self.config.get('include_sources', False):
                processed_answer = self._add_source_references(
                    processed_answer, retrieval_results, web_results
                )
            
            return processed_answer
            
        except Exception as e:
            logger.error(f"Erreur post-traitement: {e}")
            return answer
    
    def _add_source_references(self,
                             answer: str,
                             retrieval_results: List[RetrievalResult],
                             web_results: List[WebSearchResult]) -> str:
        """Ajoute des références aux sources."""
        references = []
        
        # Références aux documents
        for i, result in enumerate(retrieval_results[:3], 1):
            filename = result.metadata.get('filename', f'Document {i}')
            references.append(f"{i}. {filename}")
        
        # Références web
        start_idx = len(references) + 1
        for i, result in enumerate(web_results[:2], start_idx):
            references.append(f"{i}. {result.title} ({result.url})")
        
        if references:
            answer += "\n\n**Sources:**\n" + "\n".join(references)
        
        return answer
    
    async def generate_response_async(self,
                                    question: str,
                                    conversation_history: Optional[List[Dict[str, str]]] = None,
                                    include_web_search: Optional[bool] = None) -> RAGResponse:
        """
        Génère une réponse RAG de manière asynchrone.
        
        Args:
            question: Question de l'utilisateur
            conversation_history: Historique de conversation
            include_web_search: Forcer/empêcher la recherche web
            
        Returns:
            Réponse RAG complète
        """
        # Pour l'instant, wrapper synchrone
        # TODO: Implémenter version vraiment asynchrone
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_response,
            question,
            conversation_history,
            include_web_search
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retourne le statut du système RAG."""
        status = {
            'llm_model': self.llm_client.get_model_info(),
            'retriever_stats': self.retriever.get_statistics(),
            'web_search_enabled': self.web_search_client is not None,
            'config': self.config
        }
        
        if self.web_search_client:
            status['web_search_stats'] = self.web_search_client.get_statistics()
        
        # Test de santé
        status['health'] = {
            'llm_healthy': self.llm_client.health_check(),
            'retriever_healthy': True,  # TODO: Ajouter health check
            'web_search_healthy': True  # TODO: Ajouter health check
        }
        
        return status


# Fonctions utilitaires
def create_rag_chain(llm_client: OllamaClient,
                    retriever: DocumentRetriever,
                    web_search_client: Optional[WebSearchClient] = None,
                    config: Optional[Dict[str, Any]] = None) -> RAGChainBuilder:
    """
    Crée une chaîne RAG complète.
    
    Args:
        llm_client: Client LLM
        retriever: Récupérateur de documents
        web_search_client: Client de recherche web optionnel
        config: Configuration
        
    Returns:
        Chaîne RAG configurée
    """
    return RAGChainBuilder(llm_client, retriever, web_search_client, config)


def test_rag_chain(chain: RAGChainBuilder, test_question: str = "Test question") -> bool:
    """
    Teste une chaîne RAG.
    
    Args:
        chain: Chaîne RAG à tester
        test_question: Question de test
        
    Returns:
        True si le test réussit
    """
    try:
        response = chain.generate_response(test_question)
        return len(response.answer) > 0 and "erreur" not in response.answer.lower()
    except Exception as e:
        logger.error(f"Test de chaîne RAG échoué: {e}")
        return False 