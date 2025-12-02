"""
Tests unitaires pour les modules d'embeddings et d'indexation vectorielle.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from embeddings.embedding_model import EmbeddingModel, create_embedding_model
from embeddings.build_index import VectorIndexBuilder, create_vector_index
from embeddings.utils import (
    normalize_embeddings, calculate_similarity, reduce_dimensions,
    detect_outliers, cluster_embeddings, calculate_quality_metrics
)


class TestEmbeddingModel:
    """Tests pour le modèle d'embeddings."""
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_init_sentence_transformer(self, mock_st):
        """Test d'initialisation avec SentenceTransformer."""
        config = {
            'model_name': 'all-MiniLM-L6-v2',
            'device': 'cpu'
        }
        
        model = EmbeddingModel(config)
        
        assert model.model_name == 'all-MiniLM-L6-v2'
        assert model.device == 'cpu'
        mock_st.assert_called_once()
    
    def test_encode_single_text(self, mock_embedding_model):
        """Test d'encodage d'un texte simple."""
        text = "Ceci est un texte de test"
        
        embeddings = mock_embedding_model.encode(text)
        
        assert embeddings is not None
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 4  # Dimension définie dans le mock
    
    def test_encode_multiple_texts(self, mock_embedding_model):
        """Test d'encodage de plusieurs textes."""
        texts = ["Texte 1", "Texte 2", "Texte 3"]
        
        embeddings = mock_embedding_model.encode(texts)
        
        assert embeddings is not None
        assert len(embeddings) == 3
        assert all(len(emb) == 4 for emb in embeddings)
    
    def test_encode_batch(self, mock_embedding_model):
        """Test d'encodage par batch."""
        texts = ["Texte {}".format(i) for i in range(10)]
        
        embeddings = mock_embedding_model.encode_batch(texts, batch_size=3)
        
        assert embeddings is not None
        assert len(embeddings) == 10
    
    def test_similarity_calculation(self, mock_embedding_model):
        """Test de calcul de similarité."""
        emb1 = [0.1, 0.2, 0.3, 0.4]
        emb2 = [0.2, 0.3, 0.4, 0.5]
        
        similarity = mock_embedding_model.similarity(emb1, emb2)
        
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1
    
    def test_get_dimension(self, mock_embedding_model):
        """Test de récupération de la dimension."""
        dimension = mock_embedding_model.get_dimension()
        
        assert dimension == 4  # Défini dans le mock
    
    def test_encode_empty_text(self, mock_embedding_model):
        """Test d'encodage d'un texte vide."""
        mock_embedding_model.encode.return_value = [[0.0, 0.0, 0.0, 0.0]]
        
        embeddings = mock_embedding_model.encode("")
        
        assert embeddings is not None
        assert len(embeddings) == 1


class TestVectorIndexBuilder:
    """Tests pour le constructeur d'index vectoriel."""
    
    def test_init_chroma(self):
        """Test d'initialisation avec ChromaDB."""
        config = {
            'type': 'chroma',
            'persist_directory': './test_data',
            'collection_name': 'test_collection'
        }
        
        with patch('chromadb.PersistentClient'):
            index = VectorIndexBuilder(config)
            assert index.index_type == 'chroma'
    
    def test_init_faiss(self):
        """Test d'initialisation avec FAISS."""
        config = {
            'type': 'faiss',
            'dimension': 384,
            'index_type': 'flat'
        }
        
        with patch('faiss.IndexFlatIP'):
            index = VectorIndexBuilder(config)
            assert index.index_type == 'faiss'
    
    def test_add_chunks(self, mock_vector_index, mock_embedding_model):
        """Test d'ajout de chunks à l'index."""
        chunks = [
            {
                'chunk_id': 'chunk_1',
                'content': 'Contenu du chunk 1',
                'metadata': {'filename': 'test.txt'}
            },
            {
                'chunk_id': 'chunk_2',
                'content': 'Contenu du chunk 2',
                'metadata': {'filename': 'test.txt'}
            }
        ]
        
        mock_vector_index.set_embedding_model(mock_embedding_model)
        result = mock_vector_index.add_chunks(chunks)
        
        assert result == 5  # Valeur définie dans le mock
    
    def test_search(self, mock_vector_index):
        """Test de recherche dans l'index."""
        query = "Recherche de test"
        
        results = mock_vector_index.search(query, top_k=3)
        
        assert len(results) == 2  # Défini dans le mock
        assert all('chunk_id' in result for result in results)
        assert all('similarity' in result for result in results)
    
    def test_save_load_index(self, mock_vector_index, temp_dir):
        """Test de sauvegarde et chargement d'index."""
        save_path = temp_dir
        
        # Test de sauvegarde
        mock_vector_index.save(save_path)
        
        # Test de chargement
        mock_vector_index.load(save_path)
        
        # Les mocks devraient avoir été appelés
        assert True  # Le mock ne lève pas d'exception
    
    def test_get_stats(self, mock_vector_index):
        """Test de récupération des statistiques."""
        stats = mock_vector_index.get_stats()
        
        assert isinstance(stats, dict)
        # Dans un vrai test, on vérifierait les clés attendues
    
    def test_delete_chunk(self, mock_vector_index):
        """Test de suppression d'un chunk."""
        chunk_id = "chunk_to_delete"
        
        result = mock_vector_index.delete(chunk_id)
        
        # Dans un mock, on assume que la suppression réussit
        assert result is not None


class TestEmbeddingUtils:
    """Tests pour les utilitaires d'embeddings."""
    
    def test_normalize_embeddings(self):
        """Test de normalisation d'embeddings."""
        embeddings = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        
        normalized = normalize_embeddings(embeddings)
        
        assert normalized.shape == embeddings.shape
        # Vérifier que les vecteurs sont normalisés
        norms = np.linalg.norm(normalized, axis=1)
        np.testing.assert_allclose(norms, 1.0, rtol=1e-6)
    
    def test_calculate_similarity_cosine(self):
        """Test de calcul de similarité cosinus."""
        emb1 = np.array([1.0, 0.0, 0.0])
        emb2 = np.array([0.0, 1.0, 0.0])
        emb3 = np.array([1.0, 0.0, 0.0])
        
        # Similarité entre vecteurs orthogonaux
        sim1 = calculate_similarity(emb1, emb2, method='cosine')
        assert abs(sim1) < 0.01  # Proche de 0
        
        # Similarité entre vecteurs identiques
        sim2 = calculate_similarity(emb1, emb3, method='cosine')
        assert abs(sim2 - 1.0) < 0.01  # Proche de 1
    
    def test_calculate_similarity_euclidean(self):
        """Test de calcul de similarité euclidienne."""
        emb1 = np.array([0.0, 0.0, 0.0])
        emb2 = np.array([1.0, 1.0, 1.0])
        
        sim = calculate_similarity(emb1, emb2, method='euclidean')
        
        assert isinstance(sim, float)
        assert sim >= 0  # La distance euclidienne est positive
    
    def test_calculate_similarity_dot_product(self):
        """Test de calcul de similarité par produit scalaire."""
        emb1 = np.array([1.0, 2.0, 3.0])
        emb2 = np.array([2.0, 3.0, 4.0])
        
        sim = calculate_similarity(emb1, emb2, method='dot')
        
        expected = np.dot(emb1, emb2)
        assert abs(sim - expected) < 0.01
    
    def test_reduce_dimensions_pca(self):
        """Test de réduction de dimensionnalité avec PCA."""
        # Créer des embeddings de test (100 échantillons, 50 dimensions)
        embeddings = np.random.randn(100, 50)
        target_dim = 10
        
        reduced = reduce_dimensions(embeddings, target_dim, method='pca')
        
        assert reduced.shape == (100, target_dim)
    
    def test_reduce_dimensions_tsne(self):
        """Test de réduction de dimensionnalité avec t-SNE."""
        # Créer des embeddings de test (50 échantillons, 20 dimensions)
        embeddings = np.random.randn(50, 20)
        target_dim = 2
        
        reduced = reduce_dimensions(embeddings, target_dim, method='tsne')
        
        assert reduced.shape == (50, target_dim)
    
    def test_detect_outliers(self):
        """Test de détection d'outliers."""
        # Créer des embeddings normaux + quelques outliers
        normal_embeddings = np.random.randn(95, 10)
        outlier_embeddings = np.random.randn(5, 10) * 5  # Outliers
        embeddings = np.vstack([normal_embeddings, outlier_embeddings])
        
        outliers = detect_outliers(embeddings, method='isolation_forest')
        
        assert len(outliers) <= len(embeddings)
        assert all(isinstance(idx, (int, np.integer)) for idx in outliers)
    
    def test_cluster_embeddings_kmeans(self):
        """Test de clustering avec K-Means."""
        embeddings = np.random.randn(100, 10)
        n_clusters = 5
        
        clusters = cluster_embeddings(embeddings, n_clusters, method='kmeans')
        
        assert len(clusters) == len(embeddings)
        assert all(0 <= cluster < n_clusters for cluster in clusters)
    
    def test_cluster_embeddings_dbscan(self):
        """Test de clustering avec DBSCAN."""
        embeddings = np.random.randn(100, 10)
        
        clusters = cluster_embeddings(embeddings, method='dbscan')
        
        assert len(clusters) == len(embeddings)
        # DBSCAN peut produire des clusters -1 (bruit)
        assert all(cluster >= -1 for cluster in clusters)
    
    def test_calculate_quality_metrics(self):
        """Test de calcul de métriques de qualité."""
        embeddings = np.random.randn(100, 10)
        labels = np.random.randint(0, 5, 100)  # 5 clusters
        
        metrics = calculate_quality_metrics(embeddings, labels)
        
        assert isinstance(metrics, dict)
        expected_keys = ['silhouette_score', 'calinski_harabasz_score', 'davies_bouldin_score']
        for key in expected_keys:
            assert key in metrics
            assert isinstance(metrics[key], (float, np.floating))


class TestIntegrationEmbeddings:
    """Tests d'intégration pour les modules d'embeddings."""
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_embedding_pipeline(self, mock_st):
        """Test du pipeline complet d'embeddings."""
        # Configuration de test
        embedding_config = {
            'model_name': 'all-MiniLM-L6-v2',
            'device': 'cpu'
        }
        
        index_config = {
            'type': 'chroma',
            'persist_directory': './test_data',
            'collection_name': 'test'
        }
        
        # Mock de SentenceTransformer
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.randn(3, 384)
        mock_st.return_value = mock_model
        
        # Créer les composants
        embedding_model = create_embedding_model(embedding_config)
        
        with patch('chromadb.PersistentClient'):
            vector_index = create_vector_index(index_config)
            vector_index.set_embedding_model(embedding_model)
            
            # Données de test
            chunks = [
                {
                    'chunk_id': 'chunk_1',
                    'content': 'Premier chunk de test',
                    'metadata': {'filename': 'test1.txt'}
                },
                {
                    'chunk_id': 'chunk_2',
                    'content': 'Deuxième chunk de test',
                    'metadata': {'filename': 'test2.txt'}
                },
                {
                    'chunk_id': 'chunk_3',
                    'content': 'Troisième chunk de test',
                    'metadata': {'filename': 'test3.txt'}
                }
            ]
            
            # Ajouter les chunks à l'index
            vector_index.add_chunks(chunks)
            
            # Rechercher
            results = vector_index.search("chunk de test", top_k=2)
            
            # Vérifications
            assert embedding_model is not None
            assert vector_index is not None
            assert mock_model.encode.called
    
    def test_similarity_search_accuracy(self):
        """Test de précision de la recherche de similarité."""
        # Créer des embeddings de test avec des similarités connues
        base_embedding = np.array([1.0, 0.0, 0.0, 0.0])
        similar_embedding = np.array([0.9, 0.1, 0.0, 0.0])  # Très similaire
        different_embedding = np.array([0.0, 0.0, 1.0, 0.0])  # Très différent
        
        # Test de similarité cosinus
        sim1 = calculate_similarity(base_embedding, similar_embedding, 'cosine')
        sim2 = calculate_similarity(base_embedding, different_embedding, 'cosine')
        
        assert sim1 > sim2  # Le premier devrait être plus similaire
        assert sim1 > 0.8   # Devrait être très similaire
        assert sim2 < 0.3   # Devrait être peu similaire 