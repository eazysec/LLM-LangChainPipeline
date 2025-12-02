#!/usr/bin/env python3
"""
Script de test pour la recherche dans les index vectoriels.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from embeddings.build_index import VectorIndexBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_faiss_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Teste la recherche FAISS."""
    try:
        logger.info(f"🔍 Test FAISS - Recherche: '{query}'")
        
        # Configuration FAISS
        config = {
            "type": "faiss",
            "index_path": "data/processed/indexes/faiss_index.bin",
            "metadata_path": "data/processed/indexes/faiss_metadata.json"
        }
        
        # Initialiser le builder
        builder = VectorIndexBuilder(config)
        
        # Charger le modèle d'embeddings
        from embeddings.embedding_model import EmbeddingModel
        builder.embedding_model = EmbeddingModel()
        
        # Effectuer la recherche avec threshold plus bas
        results = builder.search(query, top_k=top_k, threshold=0.0)  # Threshold très bas
        
        logger.info(f"📊 FAISS - {len(results)} résultats trouvés:")
        
        if not results:
            # Debug : vérifier les stats de l'index
            stats = builder.get_statistics()
            print(f"🔍 DEBUG - Stats index: {stats}")
            
            # Essayer de voir les premiers éléments des métadonnées
            if hasattr(builder, 'faiss_metadata') and builder.faiss_metadata:
                print(f"🔍 DEBUG - Nombre de métadonnées: {len(builder.faiss_metadata)}")
                # Afficher les 3 premiers éléments
                for i, (idx, data) in enumerate(list(builder.faiss_metadata.items())[:3]):
                    print(f"    [{idx}]: {data.get('content', '')[:100]}...")
        
        for i, result in enumerate(results, 1):
            score = result.get('similarity', result.get('score', 0))
            content = result.get('content', '')[:200] + "..."
            source = result.get('metadata', {}).get('file_name', 'Inconnu')
            
            print(f"  {i}. Score: {score:.4f}")
            print(f"     Source: {source}")
            print(f"     Chunk: {content}")
            print("     " + "-"*50)
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur FAISS: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return []

def test_chroma_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Teste la recherche ChromaDB."""
    try:
        logger.info(f"🔍 Test ChromaDB - Recherche: '{query}'")
        
        # Configuration ChromaDB
        config = {
            "type": "chroma",
            "persist_directory": "data/processed/indexes/chroma_db",
            "collection_name": "documents"
        }
        
        # Initialiser le builder
        builder = VectorIndexBuilder(config)
        
        # Charger le modèle d'embeddings
        from embeddings.embedding_model import EmbeddingModel
        builder.embedding_model = EmbeddingModel()
        
        # Effectuer la recherche
        results = builder.search(query, top_k=top_k)
        
        logger.info(f"📊 ChromaDB - {len(results)} résultats trouvés:")
        for i, result in enumerate(results, 1):
            score = result.get('score', 0)
            content = result.get('content', '')[:200] + "..."
            source = result.get('metadata', {}).get('file_name', 'Inconnu')
            
            print(f"  {i}. Score: {score:.4f}")
            print(f"     Source: {source}")
            print(f"     Chunk: {content}")
            print("     " + "-"*50)
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur ChromaDB: {e}")
        return []

def compare_search_engines(query: str, top_k: int = 5):
    """Compare les performances FAISS vs ChromaDB."""
    import time
    
    # Test FAISS
    start_time = time.time()
    faiss_results = test_faiss_search(query, top_k)
    faiss_time = time.time() - start_time
    
    # Test ChromaDB  
    start_time = time.time()
    chroma_results = test_chroma_search(query, top_k)
    chroma_time = time.time() - start_time
    
    # Comparaison
    print(f"⚡ FAISS: {len(faiss_results)} résultats en {faiss_time:.3f}s")
    print(f"🔮 ChromaDB: {len(chroma_results)} résultats en {chroma_time:.3f}s")
    
    if faiss_time > 0 and chroma_time > 0:
        speed_diff = abs(faiss_time - chroma_time) / min(faiss_time, chroma_time) * 100
        faster = "FAISS" if faiss_time < chroma_time else "ChromaDB"
        print(f"🏆 {faster} est {speed_diff:.1f}% plus rapide")

def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test de recherche dans les index vectoriels")
    parser.add_argument("query", help="Requête de recherche")
    parser.add_argument("--engine", "-e", choices=["faiss", "chroma", "both"], 
                       default="both", help="Moteur de recherche à tester")
    parser.add_argument("--results", "-r", type=int, default=5, 
                       help="Nombre de résultats à retourner")
    
    args = parser.parse_args()
    
    print("="*60)
    print(f"🔍 TEST DE RECHERCHE: '{args.query}'")
    print("="*60)
    
    if args.engine in ["faiss", "both"]:
        print("\n" + "="*40)
        print("📊 RECHERCHE FAISS")
        print("="*40)
        faiss_results = test_faiss_search(args.query, args.results)
    
    if args.engine in ["chroma", "both"]:
        print("\n" + "="*40) 
        print("🔮 RECHERCHE CHROMADB")
        print("="*40)
        chroma_results = test_chroma_search(args.query, args.results)
    
    if args.engine == "both":
        print("\n" + "="*40)
        print("📈 COMPARAISON")
        print("="*40)
        compare_search_engines(args.query, args.results)


if __name__ == "__main__":
    main() 