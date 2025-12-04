"""
Wrapper pour les modèles d'embeddings (Sentence Transformers, OpenAI, etc.).
"""

import logging
import numpy as np
from typing import List, Union, Optional, Dict, Any
import torch
from sentence_transformers import SentenceTransformer
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Wrapper unifié pour différents modèles d'embeddings."""
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", 
                 device: str = "cpu", cache_dir: Optional[str] = None):
        """
        Initialise le modèle d'embeddings.
        
        Args:
            model_name: Nom du modèle à utiliser
            device: Device à utiliser (cpu/cuda)
            cache_dir: Répertoire de cache pour le modèle
        """
        self.model_name = model_name
        self.device = device
        self.cache_dir = cache_dir
        self.model = None
        self.embedding_dimension = None
        self.max_seq_length = None
        
        # Pool de threads pour l'encodage asynchrone
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        self._load_model()
    
    def _load_model(self):
        """Charge le modèle d'embeddings."""
        try:
            logger.info(f"Chargement du modèle d'embeddings: {self.model_name}")
            
            # Configurer le device
            if self.device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA non disponible, utilisation du CPU")
                self.device = "cpu"
            
            # Charger le modèle Sentence Transformers
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_dir
            )
            
            # Récupérer les informations du modèle
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            self.max_seq_length = self.model.max_seq_length
            
            logger.info(f"Modèle chargé - Dimension: {self.embedding_dimension}, "
                       f"Longueur max: {self.max_seq_length}")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            raise
    
    def encode(self, texts: Union[str, List[str]], 
               batch_size: int = 32, 
               normalize: bool = True,
               show_progress: bool = False) -> np.ndarray:
        """
        Encode un ou plusieurs textes en vecteurs.
        
        Args:
            texts: Texte(s) à encoder
            batch_size: Taille des lots pour l'encodage
            normalize: Si True, normalise les vecteurs
            show_progress: Afficher la barre de progression
            
        Returns:
            Vecteurs d'embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        try:
            # Préprocessing des textes
            processed_texts = self._preprocess_texts(texts)
            
            # Encodage
            embeddings = self.model.encode(
                processed_texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            
            logger.debug(f"Encodage terminé: {len(texts)} textes -> {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Erreur lors de l'encodage: {e}")
            raise
    
    async def encode_async(self, texts: Union[str, List[str]], 
                          batch_size: int = 32,
                          normalize: bool = True) -> np.ndarray:
        """
        Encode des textes de manière asynchrone.
        
        Args:
            texts: Texte(s) à encoder
            batch_size: Taille des lots
            normalize: Normaliser les vecteurs
            
        Returns:
            Vecteurs d'embeddings
        """
        loop = asyncio.get_event_loop()
        
        # Exécuter l'encodage dans un thread séparé
        embeddings = await loop.run_in_executor(
            self.executor,
            self.encode,
            texts,
            batch_size,
            normalize,
            False  # show_progress
        )
        
        return embeddings
    
    def encode_batch(self, text_batches: List[List[str]], 
                    batch_size: int = 32,
                    normalize: bool = True) -> List[np.ndarray]:
        """
        Encode plusieurs lots de textes.
        
        Args:
            text_batches: Liste de lots de textes
            batch_size: Taille des lots pour l'encodage
            normalize: Normaliser les vecteurs
            
        Returns:
            Liste de vecteurs d'embeddings
        """
        results = []
        
        for i, batch in enumerate(text_batches):
            try:
                embeddings = self.encode(batch, batch_size, normalize)
                results.append(embeddings)
                
                logger.debug(f"Lot {i+1}/{len(text_batches)} encodé: {len(batch)} textes")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'encodage du lot {i}: {e}")
                # Ajouter un tableau vide en cas d'erreur
                results.append(np.array([]))
        
        return results
    
    def _preprocess_texts(self, texts: List[str]) -> List[str]:
        """
        Préprocesse les textes avant encodage.
        
        Args:
            texts: Liste de textes à préprocesser
            
        Returns:
            Textes préprocessés
        """
        processed_texts = []
        
        for text in texts:
            if not isinstance(text, str):
                text = str(text)
            
            # Nettoyer le texte
            text = text.strip()
            
            # Limiter la longueur si nécessaire
            if self.max_seq_length and len(text) > self.max_seq_length:
                # Tronquer intelligemment (garder le début et la fin)
                half_length = self.max_seq_length // 2
                text = text[:half_length] + "..." + text[-half_length:]
            
            processed_texts.append(text)
        
        return processed_texts
    
    def similarity(self, embeddings1: np.ndarray, 
                  embeddings2: np.ndarray) -> np.ndarray:
        """
        Calcule la similarité cosinus entre deux ensembles d'embeddings.
        
        Args:
            embeddings1: Premier ensemble d'embeddings
            embeddings2: Deuxième ensemble d'embeddings
            
        Returns:
            Matrice de similarité
        """
        return np.dot(embeddings1, embeddings2.T)
    
    def find_most_similar(self, query_embedding: np.ndarray,
                         document_embeddings: np.ndarray,
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Trouve les documents les plus similaires à une requête.
        
        Args:
            query_embedding: Embedding de la requête
            document_embeddings: Embeddings des documents
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste des résultats avec scores de similarité
        """
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Calculer les similarités
        similarities = self.similarity(query_embedding, document_embeddings)[0]
        
        # Trouver les top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Créer les résultats
        results = []
        for idx in top_indices:
            results.append({
                'index': int(idx),
                'similarity': float(similarities[idx])
            })
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retourne les informations du modèle."""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'embedding_dimension': self.embedding_dimension,
            'max_seq_length': self.max_seq_length,
            'is_loaded': self.model is not None
        }
    
    def save_embeddings(self, embeddings: np.ndarray, filepath: str):
        """
        Sauvegarde les embeddings dans un fichier.
        
        Args:
            embeddings: Embeddings à sauvegarder
            filepath: Chemin du fichier
        """
        try:
            np.save(filepath, embeddings)
            logger.info(f"Embeddings sauvegardés: {filepath}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            raise
    
    def load_embeddings(self, filepath: str) -> np.ndarray:
        """
        Charge les embeddings depuis un fichier.
        
        Args:
            filepath: Chemin du fichier
            
        Returns:
            Embeddings chargés
        """
        try:
            embeddings = np.load(filepath)
            logger.info(f"Embeddings chargés: {filepath} - Shape: {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            raise
    
    def __del__(self):
        """Nettoyage lors de la destruction de l'objet."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# Fonctions utilitaires
def create_embedding_model(config: Dict[str, Any]) -> EmbeddingModel:
    """
    Crée un modèle d'embeddings depuis une configuration.
    
    Args:
        config: Configuration du modèle
        
    Returns:
        Instance du modèle d'embeddings
    """
    return EmbeddingModel(
        model_name=config.get('model_name', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'),
        device=config.get('device', 'cpu'),
        cache_dir=config.get('cache_dir')
    )


def compare_embeddings(embeddings1: np.ndarray, 
                      embeddings2: np.ndarray,
                      metric: str = 'cosine') -> np.ndarray:
    """
    Compare deux ensembles d'embeddings avec différentes métriques.
    
    Args:
        embeddings1: Premier ensemble
        embeddings2: Deuxième ensemble
        metric: Métrique à utiliser ('cosine', 'euclidean', 'dot')
        
    Returns:
        Matrice de distances/similarités
    """
    if metric == 'cosine':
        # Normaliser pour la similarité cosinus
        norm1 = embeddings1 / np.linalg.norm(embeddings1, axis=1, keepdims=True)
        norm2 = embeddings2 / np.linalg.norm(embeddings2, axis=1, keepdims=True)
        return np.dot(norm1, norm2.T)
    
    elif metric == 'euclidean':
        # Distance euclidienne
        from scipy.spatial.distance import cdist
        return cdist(embeddings1, embeddings2, metric='euclidean')
    
    elif metric == 'dot':
        # Produit scalaire
        return np.dot(embeddings1, embeddings2.T)
    
    else:
        raise ValueError(f"Métrique non supportée: {metric}")


def cluster_embeddings(embeddings: np.ndarray, 
                      n_clusters: int = 5,
                      method: str = 'kmeans') -> np.ndarray:
    """
    Groupe les embeddings en clusters.
    
    Args:
        embeddings: Embeddings à grouper
        n_clusters: Nombre de clusters
        method: Méthode de clustering ('kmeans', 'hierarchical')
        
    Returns:
        Labels des clusters
    """
    if method == 'kmeans':
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        return kmeans.fit_predict(embeddings)
    
    elif method == 'hierarchical':
        from sklearn.cluster import AgglomerativeClustering
        clustering = AgglomerativeClustering(n_clusters=n_clusters)
        return clustering.fit_predict(embeddings)
    
    else:
        raise ValueError(f"Méthode de clustering non supportée: {method}") 