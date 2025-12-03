"""
Module pour construire et gérer les index vectoriels (ChromaDB, FAISS, etc.).
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
import faiss
import pickle
import os
from pathlib import Path
import json
import uuid

from .embedding_model import EmbeddingModel
# from ..ingestion.chunking import Chunk  # Éviter l'import relatif pour les tests

# Type alias local pour éviter les problèmes d'import
Chunk = dict

logger = logging.getLogger(__name__)


class VectorIndexBuilder:
    """Constructeur d'index vectoriels pour la recherche sémantique."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le constructeur d'index.
        
        Args:
            config: Configuration de l'index
        """
        self.config = config
        self.index_type = config.get('type', 'chroma')
        self.embedding_model = None
        self.index = None
        self.metadata_store = {}
        
        # Initialiser selon le type d'index
        if self.index_type == 'chroma':
            self._init_chroma()
        elif self.index_type == 'faiss':
            self._init_faiss()
        else:
            raise ValueError(f"Type d'index non supporté: {self.index_type}")
    
    def _init_chroma(self):
        """Initialise ChromaDB."""
        try:
            persist_directory = self.config.get('persist_directory', './data/chroma_db')
            collection_name = self.config.get('collection_name', 'documents')
            
            # Créer le répertoire s'il n'existe pas
            Path(persist_directory).mkdir(parents=True, exist_ok=True)
            
            # Configurer ChromaDB
            self.chroma_client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Créer ou récupérer la collection
            try:
                self.collection = self.chroma_client.get_collection(name=collection_name)
                logger.info(f"Collection ChromaDB récupérée: {collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": "Documents pour RAG"}
                )
                logger.info(f"Collection ChromaDB créée: {collection_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de ChromaDB: {e}")
            raise
    
    def _init_faiss(self):
        """Initialise FAISS."""
        try:
            self.faiss_index = None
            self.faiss_ids = []
            self.faiss_metadata = {}
            self.index_file = self.config.get('index_file', './data/faiss_index.bin')
            self.metadata_file = self.config.get('metadata_file', './data/faiss_metadata.json')
            
            # Charger l'index existant s'il existe
            if os.path.exists(self.index_file):
                self._load_faiss_index()
                logger.info("Index FAISS chargé depuis le disque")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de FAISS: {e}")
            raise
    
    def set_embedding_model(self, embedding_model: EmbeddingModel):
        """
        Définit le modèle d'embeddings à utiliser.
        
        Args:
            embedding_model: Modèle d'embeddings
        """
        self.embedding_model = embedding_model
        logger.info(f"Modèle d'embeddings défini: {embedding_model.model_name}")
    
    def add_chunks(self, chunks: List[Chunk], batch_size: int = 100) -> int:
        """
        Ajoute des chunks à l'index vectoriel.
        
        Args:
            chunks: Liste de chunks à indexer
            batch_size: Taille des lots pour le traitement
            
        Returns:
            Nombre de chunks ajoutés
        """
        if not self.embedding_model:
            raise ValueError("Modèle d'embeddings non défini")
        
        if not chunks:
            logger.warning("Aucun chunk à ajouter")
            return 0
        
        try:
            added_count = 0
            
            # Traiter par lots
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                
                # Extraire les textes
                texts = [chunk.content for chunk in batch_chunks]
                
                # Générer les embeddings
                embeddings = self.embedding_model.encode(texts, batch_size=batch_size)
                
                # Ajouter à l'index selon le type
                if self.index_type == 'chroma':
                    added_count += self._add_to_chroma(batch_chunks, embeddings)
                elif self.index_type == 'faiss':
                    added_count += self._add_to_faiss(batch_chunks, embeddings)
                
                logger.info(f"Lot {i//batch_size + 1} ajouté: {len(batch_chunks)} chunks")
            
            logger.info(f"Indexation terminée: {added_count} chunks ajoutés")
            return added_count
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des chunks: {e}")
            raise
    
    def _add_to_chroma(self, chunks: List[Chunk], embeddings: np.ndarray) -> int:
        """Ajoute des chunks à ChromaDB."""
        try:
            # Préparer les données
            ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            embeddings_list = embeddings.tolist()
            
            # Ajouter à la collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                documents=documents,
                metadatas=metadatas
            )
            
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout à ChromaDB: {e}")
            raise
    
    def _add_to_faiss(self, chunks: List[Chunk], embeddings: np.ndarray) -> int:
        """Ajoute des chunks à FAISS."""
        try:
            # Initialiser l'index FAISS s'il n'existe pas
            if self.faiss_index is None:
                dimension = embeddings.shape[1]
                self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine similarity)
                logger.info(f"Index FAISS créé avec dimension {dimension}")
            
            # Ajouter les embeddings
            self.faiss_index.add(embeddings.astype('float32'))
            
            # Stocker les métadonnées
            for chunk in chunks:
                chunk_id = len(self.faiss_ids)
                self.faiss_ids.append(chunk.chunk_id)
                self.faiss_metadata[chunk_id] = {
                    'chunk_id': chunk.chunk_id,
                    'content': chunk.content,
                    'metadata': chunk.metadata
                }
            
            # Sauvegarder l'index
            self._save_faiss_index()
            
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout à FAISS: {e}")
            raise
    
    def search(self, query: str, top_k: int = 5, 
              threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Recherche dans l'index vectoriel.
        
        Args:
            query: Requête de recherche
            top_k: Nombre de résultats à retourner
            threshold: Seuil de similarité minimum
            
        Returns:
            Liste des résultats de recherche
        """
        if not self.embedding_model:
            raise ValueError("Modèle d'embeddings non défini")
        
        try:
            # Encoder la requête
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Rechercher selon le type d'index
            if self.index_type == 'chroma':
                return self._search_chroma(query_embedding, top_k, threshold)
            elif self.index_type == 'faiss':
                return self._search_faiss(query_embedding, top_k, threshold)
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            raise
    
    def _search_chroma(self, query_embedding: np.ndarray, 
                      top_k: int, threshold: float) -> List[Dict[str, Any]]:
        """Recherche dans ChromaDB."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            search_results = []
            
            if results['ids'] and results['ids'][0]:
                for i, chunk_id in enumerate(results['ids'][0]):
                    # ChromaDB retourne des distances, convertir en similarité
                    distance = results['distances'][0][i]
                    similarity = 1 - distance  # Approximation simple
                    
                    if similarity >= threshold:
                        search_results.append({
                            'chunk_id': chunk_id,
                            'content': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'similarity': similarity,
                            'distance': distance
                        })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche ChromaDB: {e}")
            raise
    
    def _search_faiss(self, query_embedding: np.ndarray,
                     top_k: int, threshold: float) -> List[Dict[str, Any]]:
        """Recherche dans FAISS."""
        try:
            if self.faiss_index is None:
                logger.warning("Index FAISS non initialisé")
                return []
            
            # Recherche
            query_embedding = query_embedding.reshape(1, -1).astype('float32')
            similarities, indices = self.faiss_index.search(query_embedding, top_k)
            
            search_results = []
            
            for i, idx in enumerate(indices[0]):
                if idx != -1:  # Index valide
                    similarity = float(similarities[0][i])
                    
                    if similarity >= threshold:
                        chunk_data = self.faiss_metadata.get(idx, {})
                        search_results.append({
                            'chunk_id': chunk_data.get('chunk_id', f'chunk_{idx}'),
                            'content': chunk_data.get('content', ''),
                            'metadata': chunk_data.get('metadata', {}),
                            'similarity': similarity,
                            'faiss_index': int(idx)
                        })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche FAISS: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'index."""
        try:
            if self.index_type == 'chroma':
                count = self.collection.count()
                return {
                    'type': 'chroma',
                    'total_chunks': count,
                    'collection_name': self.collection.name
                }
            elif self.index_type == 'faiss':
                count = self.faiss_index.ntotal if self.faiss_index else 0
                return {
                    'type': 'faiss',
                    'total_chunks': count,
                    'dimension': self.faiss_index.d if self.faiss_index else 0
                }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {'error': str(e)}
    
    def _save_faiss_index(self):
        """Sauvegarde l'index FAISS."""
        try:
            if self.faiss_index:
                # Créer le répertoire parent s'il n'existe pas
                Path(self.index_file).parent.mkdir(parents=True, exist_ok=True)
                
                # Sauvegarder l'index
                faiss.write_index(self.faiss_index, self.index_file)
                
                # Sauvegarder les métadonnées
                with open(self.metadata_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'ids': self.faiss_ids,
                        'metadata': self.faiss_metadata
                    }, f, ensure_ascii=False, indent=2)
                
                logger.debug("Index FAISS sauvegardé")
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde FAISS: {e}")
            raise
    
    def _load_faiss_index(self):
        """Charge l'index FAISS."""
        try:
            if os.path.exists(self.index_file):
                self.faiss_index = faiss.read_index(self.index_file)
                
                # Charger les métadonnées
                if os.path.exists(self.metadata_file):
                    with open(self.metadata_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.faiss_ids = data.get('ids', [])
                        self.faiss_metadata = data.get('metadata', {})
                        
                        # Convertir les clés en int pour faiss_metadata
                        self.faiss_metadata = {int(k): v for k, v in self.faiss_metadata.items()}
                
                logger.info(f"Index FAISS chargé: {self.faiss_index.ntotal} vecteurs")
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement FAISS: {e}")
            raise
    
    def clear_index(self):
        """Vide l'index."""
        try:
            if self.index_type == 'chroma':
                # Supprimer tous les documents de la collection
                self.chroma_client.delete_collection(self.collection.name)
                self.collection = self.chroma_client.create_collection(
                    name=self.config.get('collection_name', 'documents')
                )
                logger.info("Collection ChromaDB vidée")
                
            elif self.index_type == 'faiss':
                # Réinitialiser l'index FAISS
                self.faiss_index = None
                self.faiss_ids = []
                self.faiss_metadata = {}
                
                # Supprimer les fichiers
                if os.path.exists(self.index_file):
                    os.remove(self.index_file)
                if os.path.exists(self.metadata_file):
                    os.remove(self.metadata_file)
                
                logger.info("Index FAISS vidé")
                
        except Exception as e:
            logger.error(f"Erreur lors du vidage de l'index: {e}")
            raise


# Fonctions utilitaires
def create_vector_index(config: Dict[str, Any]) -> VectorIndexBuilder:
    """
    Crée un constructeur d'index vectoriel depuis une configuration.
    
    Args:
        config: Configuration de l'index
        
    Returns:
        Constructeur d'index vectoriel
    """
    return VectorIndexBuilder(config)


def benchmark_search(index_builder: VectorIndexBuilder, 
                    queries: List[str], 
                    ground_truth: Optional[List[List[str]]] = None) -> Dict[str, Any]:
    """
    Évalue les performances de recherche.
    
    Args:
        index_builder: Constructeur d'index à évaluer
        queries: Liste de requêtes de test
        ground_truth: Vérité terrain (optionnel)
        
    Returns:
        Métriques de performance
    """
    import time
    
    results = {
        'total_queries': len(queries),
        'average_response_time': 0,
        'response_times': []
    }
    
    total_time = 0
    
    for i, query in enumerate(queries):
        start_time = time.time()
        
        try:
            search_results = index_builder.search(query, top_k=5)
            response_time = time.time() - start_time
            
            results['response_times'].append(response_time)
            total_time += response_time
            
        except Exception as e:
            logger.error(f"Erreur lors de la requête {i}: {e}")
            results['response_times'].append(-1)
    
    results['average_response_time'] = total_time / len(queries)
    results['min_response_time'] = min(t for t in results['response_times'] if t > 0)
    results['max_response_time'] = max(results['response_times'])
    
    return results 