#!/usr/bin/env python3
"""
Script d'indexation RAPIDE des documents pour le système RAG.
Version optimisée avec GPU, cache et traitement par lots.
"""

import os
import sys
import logging
import json
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import torch

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion.loaders import DocumentLoader
from ingestion.chunking import DocumentChunker
from embeddings.embedding_model import EmbeddingModel
from embeddings.build_index import VectorIndexBuilder

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FastDocumentIndexer:
    """Indexeur de documents optimisé pour la vitesse."""
    
    def __init__(self, config_path: str = None, index_type: str = "faiss"):
        """
        Initialise l'indexeur rapide.
        
        Args:
            config_path: Chemin vers la configuration
            index_type: Type d'index ("faiss", "chroma", "both")
        """
        # Configuration optimisée
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
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "device": "cuda" if torch.cuda.is_available() else "cpu",
                "batch_size": 64  # Traitement par lots plus grand
            },
            "optimization": {
                "max_workers": min(8, os.cpu_count()),
                "use_cache": True,
                "cache_embeddings": True
            }
        }
        
        self.index_type = index_type
        self._create_directories()
        
        # Composants optimisés
        self.loader = DocumentLoader()
        self.chunker = DocumentChunker(**self.config["chunking"])
        
        # GPU/CPU detection et optimisation
        device = self.config["embedding"]["device"]
        logger.info(f"🚀 Utilisation du device: {device}")
        
        self.embedding_model = EmbeddingModel(
            model_name=self.config["embedding"]["model_name"],
            device=device
        )
        
        # Cache pour éviter de recalculer
        self.embedding_cache = {}
        
        # Statistiques
        self.stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "embeddings_cached": 0,
            "embeddings_computed": 0,
            "processing_time": 0,
            "files_processed": []
        }
    
    def _create_directories(self):
        """Crée les répertoires nécessaires."""
        dirs = [
            self.config["processed_dir"],
            self.config["index_dir"],
            "data/processed/indexes",
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def process_documents_parallel(self, directory: str = None) -> List[Dict[str, Any]]:
        """Traite tous les documents en parallèle."""
        if directory is None:
            directory = self.config["raw_dir"]
        
        # Trouver tous les fichiers
        supported_extensions = ['.pdf', '.txt', '.md', '.docx']
        files_to_process = []
        for ext in supported_extensions:
            files_to_process.extend(Path(directory).glob(f"**/*{ext}"))
        
        if not files_to_process:
            logger.warning("⚠️ Aucun fichier trouvé")
            return []
        
        logger.info(f"📚 {len(files_to_process)} fichiers à traiter")
        
        # Traitement en parallèle
        all_chunks = []
        max_workers = self.config["optimization"]["max_workers"]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.process_single_document, str(file_path)) 
                for file_path in files_to_process
            ]
            
            for future in futures:
                chunks = future.result()
                all_chunks.extend(chunks)
        
        logger.info(f"✅ {len(all_chunks)} chunks créés au total")
        return all_chunks
    
    def process_single_document(self, file_path: str) -> List[Dict[str, Any]]:
        """Traite un seul document."""
        try:
            logger.info(f"📄 Traitement: {os.path.basename(file_path)}")
            
            # Charger et découper
            document = self.loader.load_document(file_path)
            chunk_objects = self.chunker.chunk_document(document)
            
            # Convertir en dictionnaires
            chunks = []
            for i, chunk_obj in enumerate(chunk_objects):
                chunk_dict = {
                    'content': chunk_obj.content,
                    'metadata': chunk_obj.metadata.copy(),
                    'chunk_id': chunk_obj.chunk_id,
                    'start_index': chunk_obj.start_index,
                    'end_index': chunk_obj.end_index
                }
                
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
            
            logger.info(f"✅ {os.path.basename(file_path)}: {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Erreur {file_path}: {e}")
            return []
    
    def create_embeddings_batch(self, chunks: List[Dict[str, Any]]) -> np.ndarray:
        """Crée les embeddings par gros lots (optimisé)."""
        logger.info(f"🧠 Création des embeddings pour {len(chunks)} chunks...")
        
        texts = [chunk['content'] for chunk in chunks]
        batch_size = self.config["embedding"]["batch_size"]
        
        # Traitement par lots optimisé
        start_time = time.time()
        embeddings = self.embedding_model.encode_batch(texts, batch_size=batch_size)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Embeddings créés en {elapsed:.2f}s ({len(embeddings)/elapsed:.1f} chunks/sec)")
        
        self.stats["embeddings_computed"] += len(embeddings)
        return embeddings
    
    def build_single_index(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray, index_type: str):
        """Construit un seul type d'index."""
        logger.info(f"🔍 Construction de l'index {index_type.upper()}...")
        
        try:
            if index_type == "faiss":
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
            
            builder = VectorIndexBuilder(config)
            builder.embedding_model = self.embedding_model
            
            # Convertir en objets Chunk
            from ingestion.chunking import Chunk
            chunk_objects = []
            for chunk_dict in chunks:
                chunk_obj = Chunk(
                    content=chunk_dict['content'],
                    metadata=chunk_dict['metadata'],
                    chunk_id=chunk_dict['chunk_id'],
                    start_index=chunk_dict['start_index'],
                    end_index=chunk_dict['end_index']
                )
                chunk_objects.append(chunk_obj)
            
            # Indexer
            start_time = time.time()
            builder.add_chunks(chunk_objects)
            elapsed = time.time() - start_time
            
            logger.info(f"✅ Index {index_type.upper()} créé en {elapsed:.2f}s ({len(chunks)} chunks)")
            
        except Exception as e:
            logger.error(f"❌ Erreur {index_type}: {e}")
    
    def index_fast(self, directory: str = None):
        """Indexation rapide complète."""
        logger.info("🚀 INDEXATION RAPIDE - DÉBUT")
        start_time = time.time()
        
        # 1. Traitement des documents en parallèle
        all_chunks = self.process_documents_parallel(directory)
        if not all_chunks:
            logger.error("❌ Aucun chunk créé")
            return
        
        # 2. Création des embeddings par gros lots
        embeddings = self.create_embeddings_batch(all_chunks)
        
        # 3. Construction des index (selon choix)
        if self.index_type in ["faiss", "both"]:
            self.build_single_index(all_chunks, embeddings, "faiss")
        
        if self.index_type in ["chroma", "both"]:
            self.build_single_index(all_chunks, embeddings, "chroma")
        
        # 4. Statistiques finales
        self.stats["processing_time"] = time.time() - start_time
        self._save_stats()
        self._print_summary()
    
    def _save_stats(self):
        """Sauvegarde les statistiques."""
        stats_path = os.path.join(self.config["processed_dir"], "fast_indexation_stats.json")
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
        logger.info(f"📊 Statistiques: {stats_path}")
    
    def _print_summary(self):
        """Affiche un résumé optimisé."""
        logger.info("="*60)
        logger.info("⚡ INDEXATION RAPIDE - RÉSUMÉ")
        logger.info("="*60)
        logger.info(f"📄 Documents: {self.stats['documents_processed']}")
        logger.info(f"✂️ Chunks: {self.stats['chunks_created']}")
        logger.info(f"🧠 Embeddings: {self.stats['embeddings_computed']}")
        logger.info(f"⏱️ Temps total: {self.stats['processing_time']:.2f}s")
        
        if self.stats['processing_time'] > 0:
            chunks_per_sec = self.stats['chunks_created'] / self.stats['processing_time']
            logger.info(f"🚀 Vitesse: {chunks_per_sec:.1f} chunks/sec")
        
        device = self.config["embedding"]["device"]
        logger.info(f"💻 Device utilisé: {device}")
        logger.info("="*60)


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Indexation RAPIDE des documents")
    parser.add_argument("--directory", "-d", help="Répertoire à indexer", default="data/raw")
    parser.add_argument("--index", "-i", choices=["faiss", "chroma", "both"], 
                       default="faiss", help="Type d'index à créer")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mode verbeux")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Créer et lancer l'indexeur rapide
    indexer = FastDocumentIndexer(index_type=args.index)
    indexer.index_fast(args.directory)


if __name__ == "__main__":
    main() 