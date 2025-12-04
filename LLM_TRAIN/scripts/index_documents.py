#!/usr/bin/env python3
"""
Script d'indexation des documents pour le système RAG.
Traite les PDFs, les découpe en chunks et crée des index vectoriels.
"""

import os
import sys
import logging
import json
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion.loaders import DocumentLoader
from ingestion.chunking import DocumentChunker
from embeddings.embedding_model import EmbeddingModel
from embeddings.build_index import VectorIndexBuilder

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('indexation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocumentIndexer:
    """Classe principale pour indexer les documents."""
    
    def __init__(self, config_path: str = None):
        """Initialise l'indexeur avec la configuration."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Configuration par défaut
            self.config = {
                "data_dir": "data",
                "raw_dir": "data/raw",
                "processed_dir": "data/processed",
                "index_dir": "data/processed/indexes",
                "chunking": {
                    "chunk_size": 500,
                    "chunk_overlap": 50,
                    "min_chunk_size": 50
                },
                "embedding": {
                    "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                    "device": "cpu"
                },
                "indexes": {
                    "faiss": {
                        "type": "faiss",
                        "index_path": "data/processed/indexes/faiss_index.bin",
                        "metadata_path": "data/processed/indexes/faiss_metadata.json"
                    },
                    "chroma": {
                        "type": "chroma",
                        "persist_directory": "data/processed/indexes/chroma_db",
                        "collection_name": "documents"
                    }
                }
            }
        
        # Créer les répertoires nécessaires
        self._create_directories()
        
        # Initialiser les composants
        self.loader = DocumentLoader()
        self.chunker = DocumentChunker(**self.config["chunking"])
        self.embedding_model = EmbeddingModel(**self.config["embedding"])
        
        # Statistiques
        self.stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "processing_time": 0,
            "files_processed": []
        }
    
    def _create_directories(self):
        """Crée les répertoires nécessaires."""
        dirs_to_create = [
            self.config["processed_dir"],
            self.config["index_dir"],
            os.path.dirname(self.config["indexes"]["faiss"]["index_path"]),
            self.config["indexes"]["chroma"]["persist_directory"]
        ]
        
        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def process_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Traite un document : chargement et découpage en chunks.
        
        Args:
            file_path: Chemin vers le document
            
        Returns:
            Liste des chunks créés (convertis en dictionnaires)
        """
        logger.info(f"📄 Traitement du document: {file_path}")
        
        try:
            # Charger le document
            document = self.loader.load_document(file_path)
            logger.info(f"✅ Document chargé: {len(document['content'])} caractères")
            
            # Découper en chunks
            chunk_objects = self.chunker.chunk_document(document)
            logger.info(f"✂️ Document découpé en {len(chunk_objects)} chunks")
            
            # Convertir les objets Chunk en dictionnaires
            chunks = []
            for i, chunk_obj in enumerate(chunk_objects):
                # Convertir l'objet Chunk en dictionnaire
                chunk_dict = {
                    'content': chunk_obj.content,
                    'metadata': chunk_obj.metadata.copy(),
                    'chunk_id': chunk_obj.chunk_id,
                    'start_index': chunk_obj.start_index,
                    'end_index': chunk_obj.end_index
                }
                
                # Ajouter des métadonnées enrichies
                chunk_dict['metadata'].update({
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'chunk_index': i,
                    'total_chunks': len(chunk_objects),
                    'file_size': os.path.getsize(file_path)
                })
                
                chunks.append(chunk_dict)
            
            self.stats["documents_processed"] += 1
            self.stats["chunks_created"] += len(chunks)
            self.stats["files_processed"].append(file_path)
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de {file_path}: {e}")
            return []
    
    def create_embeddings(self, chunks: List[Dict[str, Any]]) -> List[np.ndarray]:
        """
        Crée les embeddings pour une liste de chunks.
        
        Args:
            chunks: Liste des chunks
            
        Returns:
            Liste des embeddings
        """
        logger.info(f"🧠 Création des embeddings pour {len(chunks)} chunks...")
        
        texts = [chunk['content'] for chunk in chunks]
        embeddings = self.embedding_model.encode_batch(texts)
        
        logger.info(f"✅ Embeddings créés: {len(embeddings)} vecteurs de dimension {embeddings[0].shape[0]}")
        return embeddings
    
    def build_faiss_index(self, chunks: List[Dict[str, Any]], embeddings: List[np.ndarray]):
        """Construit l'index FAISS."""
        logger.info("🔍 Construction de l'index FAISS...")
        
        try:
            faiss_config = self.config["indexes"]["faiss"]
            
            # Construire l'index avec le modèle d'embeddings
            builder = VectorIndexBuilder(faiss_config)
            builder.embedding_model = self.embedding_model  # Passer le modèle d'embeddings
            
            # Convertir les dictionnaires en objets Chunk pour FAISS
            from ingestion.chunking import Chunk
            chunk_objects = []
            for i, chunk_dict in enumerate(chunks):
                chunk_obj = Chunk(
                    content=chunk_dict['content'],
                    metadata=chunk_dict['metadata'],
                    chunk_id=chunk_dict['chunk_id'],
                    start_index=chunk_dict['start_index'],
                    end_index=chunk_dict['end_index']
                )
                chunk_objects.append(chunk_obj)
            
            # Ajouter les chunks à l'index
            builder.add_chunks(chunk_objects)
            
            logger.info(f"✅ Index FAISS créé avec {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"❌ Erreur FAISS: {e}")
    
    def build_chroma_index(self, chunks: List[Dict[str, Any]]):
        """Construit l'index ChromaDB."""
        logger.info("🔍 Construction de l'index ChromaDB...")
        
        try:
            chroma_config = self.config["indexes"]["chroma"]
            
            # Construire l'index avec le modèle d'embeddings
            builder = VectorIndexBuilder(chroma_config)
            builder.embedding_model = self.embedding_model  # Passer le modèle d'embeddings
            
            # Convertir les dictionnaires en objets Chunk pour ChromaDB
            from ingestion.chunking import Chunk
            chunk_objects = []
            for i, chunk_dict in enumerate(chunks):
                chunk_obj = Chunk(
                    content=chunk_dict['content'],
                    metadata=chunk_dict['metadata'],
                    chunk_id=chunk_dict['chunk_id'],
                    start_index=chunk_dict['start_index'],
                    end_index=chunk_dict['end_index']
                )
                chunk_objects.append(chunk_obj)
            
            # Ajouter les chunks à l'index (ChromaDB gère les embeddings automatiquement)
            builder.add_chunks(chunk_objects)
            
            logger.info(f"✅ Index ChromaDB créé avec {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"❌ Erreur ChromaDB: {e}")
    
    def index_directory(self, directory: str = None):
        """
        Indexe tous les documents d'un répertoire.
        
        Args:
            directory: Répertoire à indexer (par défaut: data/raw)
        """
        if directory is None:
            directory = self.config["raw_dir"]
        
        logger.info(f"🚀 Début de l'indexation du répertoire: {directory}")
        start_time = time.time()
        
        # Trouver tous les fichiers supportés
        supported_extensions = ['.pdf', '.txt', '.md', '.docx']
        files_to_process = []
        
        for ext in supported_extensions:
            files_to_process.extend(Path(directory).glob(f"**/*{ext}"))
        
        if not files_to_process:
            logger.warning("⚠️ Aucun fichier trouvé à indexer")
            return
        
        logger.info(f"📚 {len(files_to_process)} fichiers trouvés: {[f.name for f in files_to_process]}")
        
        # Traiter tous les documents
        all_chunks = []
        for file_path in files_to_process:
            chunks = self.process_document(str(file_path))
            all_chunks.extend(chunks)
        
        if not all_chunks:
            logger.error("❌ Aucun chunk créé")
            return
        
        # Créer les embeddings
        embeddings = self.create_embeddings(all_chunks)
        
        # Construire les index
        self.build_faiss_index(all_chunks, embeddings)
        self.build_chroma_index(all_chunks)
        
        # Sauvegarder les statistiques
        self.stats["processing_time"] = time.time() - start_time
        self._save_stats()
        
        logger.info("🎉 Indexation terminée !")
        self._print_summary()
    
    def _save_stats(self):
        """Sauvegarde les statistiques."""
        stats_path = os.path.join(self.config["processed_dir"], "indexation_stats.json")
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
        logger.info(f"📊 Statistiques sauvegardées: {stats_path}")
    
    def _print_summary(self):
        """Affiche un résumé de l'indexation."""
        logger.info("="*60)
        logger.info("📊 RÉSUMÉ DE L'INDEXATION")
        logger.info("="*60)
        logger.info(f"📄 Documents traités: {self.stats['documents_processed']}")
        logger.info(f"✂️ Chunks créés: {self.stats['chunks_created']}")
        logger.info(f"⏱️ Temps de traitement: {self.stats['processing_time']:.2f} secondes")
        logger.info(f"📁 Fichiers traités:")
        for file_path in self.stats['files_processed']:
            logger.info(f"   - {os.path.basename(file_path)}")
        logger.info("="*60)


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Indexation des documents pour le système RAG")
    parser.add_argument("--directory", "-d", help="Répertoire à indexer", default="data/raw")
    parser.add_argument("--config", "-c", help="Fichier de configuration JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mode verbeux")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Créer et lancer l'indexeur
    indexer = DocumentIndexer(args.config)
    indexer.index_directory(args.directory)


if __name__ == "__main__":
    main() 