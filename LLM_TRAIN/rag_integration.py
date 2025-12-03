#!/usr/bin/env python3
"""
Module d'intégration RAG pour connecter la recherche documentaire au chatbot.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional

# Ajouter le chemin du projet
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from embeddings.build_index import VectorIndexBuilder
from embeddings.embedding_model import EmbeddingModel

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRAG:
    """
    Service RAG simple pour la recherche documentaire.
    """
    
    def __init__(self, index_type: str = "faiss"):
        """
        Initialise le service RAG.
        
        Args:
            index_type: Type d'index à utiliser ("faiss" ou "chroma")
        """
        self.index_type = index_type
        self.vector_builder = None
        self.embedding_model = None
        self._initialize()
    
    def _initialize(self):
        """Initialise les composants RAG."""
        try:
            logger.info(f"🔍 Initialisation RAG avec index {self.index_type}")
            
            # Configuration selon le type d'index
            if self.index_type == "faiss":
                config = {
                    "type": "faiss",
                    "index_path": "data/processed/indexes/faiss_index.bin",
                    "metadata_path": "data/processed/indexes/faiss_metadata.json"
                }
            else:  # chroma
                config = {
                    "type": "chroma",
                    "persist_directory": "data/processed/indexes/chroma_db",
                    "collection_name": "documents"
                }
            
            # Initialiser le builder vectoriel
            self.vector_builder = VectorIndexBuilder(config)
            
            # Charger le modèle d'embeddings
            self.embedding_model = EmbeddingModel()
            self.vector_builder.embedding_model = self.embedding_model
            
            # Vérifier que l'index existe
            stats = self.vector_builder.get_statistics()
            total_chunks = stats.get('total_chunks', 0)
            
            if total_chunks > 0:
                logger.info(f"✅ RAG initialisé: {total_chunks} chunks disponibles")
            else:
                logger.warning("⚠️ Index vide - aucun document trouvé")
                
        except Exception as e:
            logger.error(f"❌ Erreur initialisation RAG: {e}")
            self.vector_builder = None
    
    def search_documents(self, query: str, top_k: int = 5, min_score: float = 0.3) -> List[Dict[str, Any]]:
        """
        Recherche des documents pertinents pour une requête.
        
        Args:
            query: Question ou requête de l'utilisateur
            top_k: Nombre max de résultats à retourner
            min_score: Score minimum pour filtrer les résultats
            
        Returns:
            Liste des chunks pertinents avec métadonnées
        """
        if not self.vector_builder:
            logger.warning("⚠️ RAG non initialisé")
            return []
        
        try:
            logger.info(f"🔍 Recherche RAG: '{query}'")
            
            # Effectuer la recherche avec threshold bas
            results = self.vector_builder.search(query, top_k=top_k, threshold=0.0)
            
            # Filtrer les résultats selon le score minimum
            filtered_results = []
            for result in results:
                score = result.get('similarity', result.get('score', 0))
                if score >= min_score:
                    filtered_results.append(result)
            
            logger.info(f"📊 RAG trouvé: {len(filtered_results)} chunks pertinents (score >= {min_score})")
            return filtered_results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche RAG: {e}")
            return []
    
    def create_context(self, search_results: List[Dict[str, Any]], max_context_length: int = 2000) -> str:
        """
        Crée un contexte textuel à partir des résultats de recherche.
        
        Args:
            search_results: Résultats de la recherche
            max_context_length: Longueur max du contexte
            
        Returns:
            Contexte formaté pour le LLM
        """
        if not search_results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(search_results, 1):
            content = result.get('content', '')
            source = result.get('metadata', {}).get('file_name', 'Source inconnue')
            score = result.get('similarity', result.get('score', 0))
            
            # Formatter la partie contexte
            context_part = f"📚 Source {i}: {source} (score: {score:.3f})\n{content}\n"
            
            # Vérifier la longueur
            if current_length + len(context_part) > max_context_length:
                break
            
            context_parts.append(context_part)
            current_length += len(context_part)
        
        return "\n".join(context_parts)
    
    def get_rag_response_context(self, user_question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Génère un contexte RAG pour répondre à une question utilisateur.
        
        Args:
            user_question: Question de l'utilisateur
            top_k: Nombre de chunks à récupérer
            
        Returns:
            Dictionnaire avec le contexte et les métadonnées
        """
        # Rechercher des documents pertinents
        search_results = self.search_documents(user_question, top_k=top_k)
        
        # Créer le contexte textuel
        context = self.create_context(search_results)
        
        # Extraire les sources
        sources = []
        for result in search_results:
            source_info = {
                'file_name': result.get('metadata', {}).get('file_name', 'Inconnu'),
                'score': result.get('similarity', result.get('score', 0)),
                'chunk_id': result.get('chunk_id', '')
            }
            if source_info not in sources:
                sources.append(source_info)
        
        return {
            'context': context,
            'sources': sources,
            'num_results': len(search_results),
            'has_context': len(context) > 0
        }
    
    def is_available(self) -> bool:
        """Vérifie si le service RAG est disponible."""
        return self.vector_builder is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du service RAG."""
        if not self.vector_builder:
            return {
                'available': False,
                'error': 'RAG non initialisé'
            }
        
        try:
            stats = self.vector_builder.get_statistics()
            return {
                'available': True,
                'index_type': self.index_type,
                'total_chunks': stats.get('total_chunks', 0),
                'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2'
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }


# Instance globale pour l'usage facile
rag_service = None

def init_rag_service(index_type: str = "faiss") -> SimpleRAG:
    """Initialise le service RAG global."""
    global rag_service
    rag_service = SimpleRAG(index_type=index_type)
    return rag_service

def get_rag_service() -> Optional[SimpleRAG]:
    """Retourne l'instance RAG globale."""
    return rag_service


if __name__ == "__main__":
    # Test du service RAG
    print("🧪 Test du service RAG")
    
    rag = SimpleRAG("faiss")
    
    # Test de recherche
    test_queries = [
        "John Dee alchimie",
        "tablette Thoth hermétique",
        "mystères secrets anciens"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Test: '{query}'")
        context_data = rag.get_rag_response_context(query)
        
        print(f"📊 Résultats: {context_data['num_results']}")
        print(f"📚 Sources: {[s['file_name'] for s in context_data['sources']]}")
        
        if context_data['has_context']:
            print(f"📄 Contexte ({len(context_data['context'])} chars):")
            print(context_data['context'][:300] + "..." if len(context_data['context']) > 300 else context_data['context'])
        else:
            print("❌ Aucun contexte trouvé") 