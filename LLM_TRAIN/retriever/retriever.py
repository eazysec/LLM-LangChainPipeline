"""
Module principal de récupération des documents pour le système RAG.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
from dataclasses import dataclass

from embeddings.embedding_model import EmbeddingModel
from embeddings.build_index import VectorIndexBuilder
from retriever.query_expansion import QueryExpander
from retriever.filters import MetadataFilter

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Résultat de récupération de documents."""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    similarity: float
    rank: int


class DocumentRetriever:
    """Récupérateur de documents pour la recherche sémantique."""
    
    def __init__(self, 
                 embedding_model: EmbeddingModel,
                 vector_index: VectorIndexBuilder,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialise le récupérateur.
        
        Args:
            embedding_model: Modèle d'embeddings
            vector_index: Index vectoriel
            config: Configuration du récupérateur
        """
        self.embedding_model = embedding_model
        self.vector_index = vector_index
        self.config = config or {}
        
        # Configuration par défaut
        self.default_top_k = self.config.get('top_k', 5)
        self.default_threshold = self.config.get('similarity_threshold', 0.7)
        self.max_results = self.config.get('max_results', 20)
        
        # Expansion de requête (optionnel)
        self.query_expander = None
        if self.config.get('enable_query_expansion', False):
            self.query_expander = QueryExpander(self.config.get('query_expansion', {}))
        
        # Filtres de métadonnées
        self.metadata_filters = []
        
        logger.info("Récupérateur de documents initialisé")
    
    def retrieve(self, query: str, 
                top_k: Optional[int] = None,
                threshold: Optional[float] = None,
                filters: Optional[List[MetadataFilter]] = None,
                rerank: bool = True) -> List[RetrievalResult]:
        """
        Récupère les documents les plus pertinents pour une requête.
        
        Args:
            query: Requête de l'utilisateur
            top_k: Nombre de résultats à retourner
            threshold: Seuil de similarité minimum
            filters: Filtres de métadonnées à appliquer
            rerank: Si True, réordonne les résultats
            
        Returns:
            Liste des résultats de récupération
        """
        try:
            # Utiliser les valeurs par défaut si non spécifiées
            top_k = top_k or self.default_top_k
            threshold = threshold or self.default_threshold
            
            # Étendre la requête si configuré
            expanded_queries = self._expand_query(query)
            
            # Récupérer les documents pour chaque requête
            all_results = []
            for expanded_query in expanded_queries:
                results = self._search_documents(expanded_query, top_k * 2, threshold)
                all_results.extend(results)
            
            # Supprimer les doublons
            unique_results = self._deduplicate_results(all_results)
            
            # Appliquer les filtres
            if filters:
                unique_results = self._apply_filters(unique_results, filters)
            
            # Réordonner si demandé
            if rerank:
                unique_results = self._rerank_results(unique_results, query)
            
            # Limiter le nombre de résultats
            final_results = unique_results[:top_k]
            
            # Créer les objets de résultat
            retrieval_results = []
            for i, result in enumerate(final_results):
                retrieval_results.append(RetrievalResult(
                    chunk_id=result['chunk_id'],
                    content=result['content'],
                    metadata=result['metadata'],
                    similarity=result['similarity'],
                    rank=i + 1
                ))
            
            logger.info(f"Récupération terminée: {len(retrieval_results)} résultats pour '{query[:50]}...'")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération: {e}")
            raise
    
    def _expand_query(self, query: str) -> List[str]:
        """Étend la requête avec des synonymes ou reformulations."""
        if self.query_expander:
            try:
                expanded = self.query_expander.expand(query)
                logger.debug(f"Requête étendue: {query} -> {len(expanded)} variations")
                return expanded
            except Exception as e:
                logger.warning(f"Erreur lors de l'expansion de requête: {e}")
        
        return [query]
    
    def _search_documents(self, query: str, top_k: int, threshold: float) -> List[Dict[str, Any]]:
        """Recherche les documents dans l'index vectoriel."""
        try:
            results = self.vector_index.search(query, top_k, threshold)
            logger.debug(f"Recherche vectorielle: {len(results)} résultats")
            return results
        except Exception as e:
            logger.error(f"Erreur lors de la recherche vectorielle: {e}")
            return []
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Supprime les résultats dupliqués."""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            chunk_id = result.get('chunk_id')
            if chunk_id and chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_results.append(result)
        
        logger.debug(f"Déduplication: {len(results)} -> {len(unique_results)} résultats")
        return unique_results
    
    def _apply_filters(self, results: List[Dict[str, Any]], 
                      filters: List[MetadataFilter]) -> List[Dict[str, Any]]:
        """Applique les filtres de métadonnées."""
        filtered_results = results
        
        for filter_obj in filters:
            filtered_results = filter_obj.apply(filtered_results)
            logger.debug(f"Filtre {filter_obj.__class__.__name__}: {len(filtered_results)} résultats")
        
        return filtered_results
    
    def _rerank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Réordonne les résultats selon différents critères."""
        try:
            # Réordonner par similarité et fraîcheur
            def ranking_score(result):
                similarity = result.get('similarity', 0)
                
                # Bonus pour la fraîcheur (si disponible)
                freshness_bonus = 0
                if 'metadata' in result and 'modified_at' in result['metadata']:
                    try:
                        modified_time = result['metadata']['modified_at']
                        if isinstance(modified_time, (int, float)):
                            days_old = (datetime.now().timestamp() - modified_time) / 86400
                            freshness_bonus = max(0, 0.1 * (1 - days_old / 365))  # Bonus sur 1 an
                    except:
                        pass
                
                # Bonus pour la longueur (contenu plus substantiel)
                length_bonus = 0
                content_length = len(result.get('content', ''))
                if content_length > 100:
                    length_bonus = min(0.05, content_length / 10000)
                
                return similarity + freshness_bonus + length_bonus
            
            # Trier par score
            reranked = sorted(results, key=ranking_score, reverse=True)
            logger.debug("Résultats réordonnés")
            
            return reranked
            
        except Exception as e:
            logger.warning(f"Erreur lors du réordonnancement: {e}")
            return results
    
    def retrieve_with_context(self, query: str, 
                             conversation_history: Optional[List[Dict[str, str]]] = None,
                             **kwargs) -> List[RetrievalResult]:
        """
        Récupère les documents en tenant compte du contexte de conversation.
        
        Args:
            query: Requête actuelle
            conversation_history: Historique de conversation
            **kwargs: Arguments supplémentaires pour retrieve()
            
        Returns:
            Liste des résultats de récupération
        """
        try:
            # Construire une requête contextuelle
            contextual_query = self._build_contextual_query(query, conversation_history)
            
            # Récupérer avec la requête contextuelle
            results = self.retrieve(contextual_query, **kwargs)
            
            logger.debug(f"Récupération contextuelle: {len(results)} résultats")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération contextuelle: {e}")
            # Fallback vers la récupération normale
            return self.retrieve(query, **kwargs)
    
    def _build_contextual_query(self, query: str, 
                               conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """Construit une requête enrichie avec le contexte."""
        if not conversation_history:
            return query
        
        # Extraire les derniers échanges
        recent_context = []
        max_context_items = self.config.get('max_context_items', 3)
        
        for item in conversation_history[-max_context_items:]:
            if item.get('role') == 'user':
                recent_context.append(item.get('content', ''))
        
        # Combiner avec la requête actuelle
        if recent_context:
            contextual_query = f"Contexte: {' '.join(recent_context[-2:])} Question: {query}"
            logger.debug(f"Requête contextuelle construite: {len(contextual_query)} caractères")
            return contextual_query
        
        return query
    
    def get_similar_chunks(self, chunk_id: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Trouve les chunks similaires à un chunk donné.
        
        Args:
            chunk_id: ID du chunk de référence
            top_k: Nombre de chunks similaires à retourner
            
        Returns:
            Liste des chunks similaires
        """
        try:
            # Cette fonctionnalité nécessiterait d'étendre l'index vectoriel
            # Pour l'instant, retour d'une liste vide
            logger.warning("Fonction get_similar_chunks pas encore implémentée")
            return []
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de chunks similaires: {e}")
            return []
    
    def add_metadata_filter(self, filter_obj: MetadataFilter):
        """Ajoute un filtre de métadonnées permanent."""
        self.metadata_filters.append(filter_obj)
        logger.info(f"Filtre ajouté: {filter_obj.__class__.__name__}")
    
    def remove_metadata_filter(self, filter_class):
        """Supprime un type de filtre de métadonnées."""
        self.metadata_filters = [f for f in self.metadata_filters if not isinstance(f, filter_class)]
        logger.info(f"Filtres {filter_class.__name__} supprimés")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du récupérateur."""
        index_stats = self.vector_index.get_statistics()
        
        return {
            'index_statistics': index_stats,
            'embedding_model': self.embedding_model.get_model_info(),
            'config': {
                'default_top_k': self.default_top_k,
                'default_threshold': self.default_threshold,
                'max_results': self.max_results,
                'query_expansion_enabled': self.query_expander is not None
            },
            'active_filters': len(self.metadata_filters)
        }


# Fonctions utilitaires
def create_retriever(embedding_model: EmbeddingModel,
                    vector_index: VectorIndexBuilder,
                    config: Optional[Dict[str, Any]] = None) -> DocumentRetriever:
    """
    Crée un récupérateur de documents.
    
    Args:
        embedding_model: Modèle d'embeddings
        vector_index: Index vectoriel
        config: Configuration du récupérateur
        
    Returns:
        Instance du récupérateur
    """
    return DocumentRetriever(embedding_model, vector_index, config)


def evaluate_retrieval_performance(retriever: DocumentRetriever,
                                  test_queries: List[str],
                                  ground_truth: List[List[str]],
                                  k_values: List[int] = [1, 3, 5, 10]) -> Dict[str, float]:
    """
    Évalue les performances de récupération.
    
    Args:
        retriever: Récupérateur à évaluer
        test_queries: Requêtes de test
        ground_truth: Documents pertinents pour chaque requête
        k_values: Valeurs de k à évaluer
        
    Returns:
        Métriques de performance
    """
    metrics = {f'precision@{k}': [] for k in k_values}
    metrics.update({f'recall@{k}': [] for k in k_values})
    metrics.update({f'mrr': []})  # Mean Reciprocal Rank
    
    for i, query in enumerate(test_queries):
        try:
            # Récupérer les documents
            results = retriever.retrieve(query, top_k=max(k_values))
            retrieved_ids = [r.chunk_id for r in results]
            
            # Documents pertinents pour cette requête
            relevant_ids = set(ground_truth[i])
            
            # Calculer les métriques pour chaque k
            for k in k_values:
                retrieved_k = set(retrieved_ids[:k])
                
                # Précision@k
                if len(retrieved_k) > 0:
                    precision = len(relevant_ids & retrieved_k) / len(retrieved_k)
                else:
                    precision = 0.0
                metrics[f'precision@{k}'].append(precision)
                
                # Rappel@k
                if len(relevant_ids) > 0:
                    recall = len(relevant_ids & retrieved_k) / len(relevant_ids)
                else:
                    recall = 0.0
                metrics[f'recall@{k}'].append(recall)
            
            # Mean Reciprocal Rank
            reciprocal_rank = 0.0
            for rank, chunk_id in enumerate(retrieved_ids, 1):
                if chunk_id in relevant_ids:
                    reciprocal_rank = 1.0 / rank
                    break
            metrics['mrr'].append(reciprocal_rank)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation de la requête {i}: {e}")
            # Ajouter des zéros pour cette requête
            for k in k_values:
                metrics[f'precision@{k}'].append(0.0)
                metrics[f'recall@{k}'].append(0.0)
            metrics['mrr'].append(0.0)
    
    # Moyenner les résultats
    final_metrics = {}
    for metric_name, values in metrics.items():
        final_metrics[metric_name] = np.mean(values) if values else 0.0
    
    return final_metrics 