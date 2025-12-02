"""
Fonctions utilitaires pour les embeddings et la recherche vectorielle.
"""

import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import pickle
import json

logger = logging.getLogger(__name__)


def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """
    Normalise les embeddings pour la similarité cosinus.
    
    Args:
        embeddings: Embeddings à normaliser
        
    Returns:
        Embeddings normalisés
    """
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # Éviter la division par zéro
    norms = np.where(norms == 0, 1, norms)
    return embeddings / norms


def cosine_similarity(embeddings1: np.ndarray, 
                     embeddings2: np.ndarray) -> np.ndarray:
    """
    Calcule la similarité cosinus entre deux ensembles d'embeddings.
    
    Args:
        embeddings1: Premier ensemble d'embeddings
        embeddings2: Deuxième ensemble d'embeddings
        
    Returns:
        Matrice de similarité cosinus
    """
    return sklearn_cosine_similarity(embeddings1, embeddings2)


def euclidean_distance(embeddings1: np.ndarray, 
                      embeddings2: np.ndarray) -> np.ndarray:
    """
    Calcule la distance euclidienne entre deux ensembles d'embeddings.
    
    Args:
        embeddings1: Premier ensemble d'embeddings
        embeddings2: Deuxième ensemble d'embeddings
        
    Returns:
        Matrice de distances euclidiennes
    """
    from scipy.spatial.distance import cdist
    return cdist(embeddings1, embeddings2, metric='euclidean')


def batch_encode(texts: List[str], 
                encoder_func: callable,
                batch_size: int = 32) -> np.ndarray:
    """
    Encode des textes par lots pour économiser la mémoire.
    
    Args:
        texts: Liste de textes à encoder
        encoder_func: Fonction d'encodage
        batch_size: Taille des lots
        
    Returns:
        Embeddings encodés
    """
    if not texts:
        return np.array([])
    
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_embeddings = encoder_func(batch_texts)
        all_embeddings.append(batch_embeddings)
        
        logger.debug(f"Lot {i//batch_size + 1} encodé: {len(batch_texts)} textes")
    
    return np.vstack(all_embeddings)


def reduce_dimensionality(embeddings: np.ndarray, 
                         method: str = 'pca',
                         n_components: int = 50) -> Tuple[np.ndarray, Any]:
    """
    Réduit la dimensionnalité des embeddings.
    
    Args:
        embeddings: Embeddings à réduire
        method: Méthode de réduction ('pca', 'tsne')
        n_components: Nombre de composantes finales
        
    Returns:
        Tuple (embeddings réduits, modèle de réduction)
    """
    if method == 'pca':
        reducer = PCA(n_components=n_components)
        reduced_embeddings = reducer.fit_transform(embeddings)
        
        logger.info(f"PCA: {embeddings.shape} -> {reduced_embeddings.shape}")
        logger.info(f"Variance expliquée: {reducer.explained_variance_ratio_.sum():.3f}")
        
    elif method == 'tsne':
        reducer = TSNE(n_components=min(n_components, 3), random_state=42)
        reduced_embeddings = reducer.fit_transform(embeddings)
        
        logger.info(f"t-SNE: {embeddings.shape} -> {reduced_embeddings.shape}")
        
    else:
        raise ValueError(f"Méthode non supportée: {method}")
    
    return reduced_embeddings, reducer


def find_outliers(embeddings: np.ndarray, 
                 threshold: float = 2.0) -> List[int]:
    """
    Trouve les embeddings aberrants basés sur la distance moyenne.
    
    Args:
        embeddings: Embeddings à analyser
        threshold: Seuil de détection (en écarts-types)
        
    Returns:
        Indices des embeddings aberrants
    """
    # Calculer les distances moyennes à tous les autres points
    distances = cosine_similarity(embeddings, embeddings)
    mean_distances = np.mean(distances, axis=1)
    
    # Trouver les outliers
    mean_dist = np.mean(mean_distances)
    std_dist = np.std(mean_distances)
    
    outliers = []
    for i, dist in enumerate(mean_distances):
        if abs(dist - mean_dist) > threshold * std_dist:
            outliers.append(i)
    
    logger.info(f"Trouvé {len(outliers)} outliers sur {len(embeddings)} embeddings")
    return outliers


def cluster_embeddings(embeddings: np.ndarray, 
                      method: str = 'kmeans',
                      n_clusters: int = 5) -> Tuple[np.ndarray, Any]:
    """
    Groupe les embeddings en clusters.
    
    Args:
        embeddings: Embeddings à grouper
        method: Méthode de clustering ('kmeans', 'dbscan', 'hierarchical')
        n_clusters: Nombre de clusters (pour kmeans et hierarchical)
        
    Returns:
        Tuple (labels des clusters, modèle de clustering)
    """
    if method == 'kmeans':
        from sklearn.cluster import KMeans
        clusterer = KMeans(n_clusters=n_clusters, random_state=42)
        labels = clusterer.fit_predict(embeddings)
        
    elif method == 'dbscan':
        from sklearn.cluster import DBSCAN
        clusterer = DBSCAN(eps=0.5, min_samples=5)
        labels = clusterer.fit_predict(embeddings)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
    elif method == 'hierarchical':
        from sklearn.cluster import AgglomerativeClustering
        clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        labels = clusterer.fit_predict(embeddings)
        
    else:
        raise ValueError(f"Méthode de clustering non supportée: {method}")
    
    logger.info(f"Clustering {method}: {len(embeddings)} points -> {n_clusters} clusters")
    return labels, clusterer


def compute_embedding_quality_metrics(embeddings: np.ndarray,
                                    labels: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calcule des métriques de qualité pour les embeddings.
    
    Args:
        embeddings: Embeddings à analyser
        labels: Labels optionnels pour l'évaluation supervisée
        
    Returns:
        Dictionnaire de métriques
    """
    metrics = {}
    
    # Métriques de base
    metrics['dimension'] = embeddings.shape[1]
    metrics['n_samples'] = embeddings.shape[0]
    metrics['mean_norm'] = np.mean(np.linalg.norm(embeddings, axis=1))
    metrics['std_norm'] = np.std(np.linalg.norm(embeddings, axis=1))
    
    # Densité locale moyenne
    similarities = cosine_similarity(embeddings, embeddings)
    np.fill_diagonal(similarities, 0)  # Exclure l'auto-similarité
    metrics['mean_similarity'] = np.mean(similarities)
    metrics['std_similarity'] = np.std(similarities)
    
    # Distribution des distances
    distances = 1 - similarities
    metrics['mean_distance'] = np.mean(distances)
    metrics['std_distance'] = np.std(distances)
    
    # Métriques intrinsèques
    try:
        # Silhouette score si on peut faire du clustering
        cluster_labels, _ = cluster_embeddings(embeddings, n_clusters=min(5, len(embeddings)//10))
        from sklearn.metrics import silhouette_score
        metrics['silhouette_score'] = silhouette_score(embeddings, cluster_labels)
    except:
        metrics['silhouette_score'] = None
    
    return metrics


def save_embeddings_with_metadata(embeddings: np.ndarray,
                                metadata: List[Dict[str, Any]],
                                filepath: str,
                                format: str = 'npz'):
    """
    Sauvegarde les embeddings avec leurs métadonnées.
    
    Args:
        embeddings: Embeddings à sauvegarder
        metadata: Métadonnées associées
        filepath: Chemin du fichier
        format: Format de sauvegarde ('npz', 'pickle')
    """
    try:
        if format == 'npz':
            # Sauvegarder en format NPZ
            np.savez_compressed(
                filepath,
                embeddings=embeddings,
                metadata=json.dumps(metadata)
            )
        elif format == 'pickle':
            # Sauvegarder en pickle
            data = {
                'embeddings': embeddings,
                'metadata': metadata
            }
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
        else:
            raise ValueError(f"Format non supporté: {format}")
        
        logger.info(f"Embeddings sauvegardés: {filepath} ({format})")
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde: {e}")
        raise


def load_embeddings_with_metadata(filepath: str,
                                 format: str = 'npz') -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Charge les embeddings avec leurs métadonnées.
    
    Args:
        filepath: Chemin du fichier
        format: Format du fichier ('npz', 'pickle')
        
    Returns:
        Tuple (embeddings, métadonnées)
    """
    try:
        if format == 'npz':
            data = np.load(filepath)
            embeddings = data['embeddings']
            metadata = json.loads(data['metadata'].item())
            
        elif format == 'pickle':
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            embeddings = data['embeddings']
            metadata = data['metadata']
            
        else:
            raise ValueError(f"Format non supporté: {format}")
        
        logger.info(f"Embeddings chargés: {filepath} - Shape: {embeddings.shape}")
        return embeddings, metadata
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement: {e}")
        raise


def interpolate_embeddings(embedding1: np.ndarray,
                          embedding2: np.ndarray,
                          alpha: float = 0.5) -> np.ndarray:
    """
    Interpole entre deux embeddings.
    
    Args:
        embedding1: Premier embedding
        embedding2: Deuxième embedding
        alpha: Facteur d'interpolation (0 = embedding1, 1 = embedding2)
        
    Returns:
        Embedding interpolé
    """
    if embedding1.shape != embedding2.shape:
        raise ValueError("Les embeddings doivent avoir la même forme")
    
    interpolated = (1 - alpha) * embedding1 + alpha * embedding2
    
    # Renormaliser si nécessaire
    norm = np.linalg.norm(interpolated)
    if norm > 0:
        interpolated = interpolated / norm
    
    return interpolated


def create_embedding_index(embeddings: np.ndarray,
                          ids: List[str],
                          method: str = 'annoy') -> Any:
    """
    Crée un index pour la recherche rapide d'embeddings.
    
    Args:
        embeddings: Embeddings à indexer
        ids: Identifiants correspondants
        method: Méthode d'indexation ('annoy', 'faiss')
        
    Returns:
        Index créé
    """
    if method == 'annoy':
        try:
            from annoy import AnnoyIndex
            
            dimension = embeddings.shape[1]
            index = AnnoyIndex(dimension, 'angular')  # Cosine distance
            
            for i, embedding in enumerate(embeddings):
                index.add_item(i, embedding)
            
            index.build(10)  # 10 trees
            logger.info(f"Index Annoy créé: {len(embeddings)} vecteurs, dimension {dimension}")
            
            return index, ids
            
        except ImportError:
            logger.error("Annoy non installé")
            raise
    
    elif method == 'faiss':
        try:
            import faiss
            
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
            
            # Normaliser les embeddings pour la similarité cosinus
            normalized_embeddings = normalize_embeddings(embeddings)
            index.add(normalized_embeddings.astype('float32'))
            
            logger.info(f"Index FAISS créé: {len(embeddings)} vecteurs, dimension {dimension}")
            
            return index, ids
            
        except ImportError:
            logger.error("FAISS non installé")
            raise
    
    else:
        raise ValueError(f"Méthode d'indexation non supportée: {method}")


def evaluate_retrieval_quality(query_embeddings: np.ndarray,
                              document_embeddings: np.ndarray,
                              relevance_labels: List[List[int]],
                              k_values: List[int] = [1, 5, 10]) -> Dict[str, List[float]]:
    """
    Évalue la qualité de récupération pour différentes valeurs de k.
    
    Args:
        query_embeddings: Embeddings des requêtes
        document_embeddings: Embeddings des documents
        relevance_labels: Labels de pertinence (liste de listes d'indices pertinents)
        k_values: Valeurs de k à évaluer
        
    Returns:
        Métriques de qualité pour chaque k
    """
    results = {f'precision@{k}': [] for k in k_values}
    results.update({f'recall@{k}': [] for k in k_values})
    results.update({f'f1@{k}': [] for k in k_values})
    
    for i, query_embedding in enumerate(query_embeddings):
        # Calculer les similarités
        similarities = cosine_similarity(
            query_embedding.reshape(1, -1),
            document_embeddings
        )[0]
        
        # Trier par similarité décroissante
        sorted_indices = np.argsort(similarities)[::-1]
        
        # Évaluer pour chaque k
        relevant_docs = set(relevance_labels[i])
        
        for k in k_values:
            retrieved_docs = set(sorted_indices[:k])
            
            # Précision
            if len(retrieved_docs) > 0:
                precision = len(relevant_docs & retrieved_docs) / len(retrieved_docs)
            else:
                precision = 0.0
            
            # Rappel
            if len(relevant_docs) > 0:
                recall = len(relevant_docs & retrieved_docs) / len(relevant_docs)
            else:
                recall = 0.0
            
            # F1-score
            if precision + recall > 0:
                f1 = 2 * (precision * recall) / (precision + recall)
            else:
                f1 = 0.0
            
            results[f'precision@{k}'].append(precision)
            results[f'recall@{k}'].append(recall)
            results[f'f1@{k}'].append(f1)
    
    # Moyenner les résultats
    for metric in results:
        results[metric] = np.mean(results[metric])
    
    return results 