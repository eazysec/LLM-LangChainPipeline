#!/usr/bin/env python3
"""
Script de démarrage du serveur ChatBot RAG.
"""

import os
import sys
import argparse
import asyncio
import logging
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from api.main import app


def setup_logging(log_level: str = "INFO"):
    """Configure le logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/chatbot_rag.log', mode='a')
        ]
    )


def create_directories():
    """Crée les répertoires nécessaires."""
    directories = [
        'data/processed',
        'data/raw', 
        'data/samples',
        'logs',
        'embeddings_cache'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Répertoire créé/vérifié: {directory}")


def check_dependencies():
    """Vérifie que les dépendances sont installées."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'sentence_transformers',
        'chromadb',
        'ollama',
        'pydantic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} est installé")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} n'est pas installé")
    
    if missing_packages:
        print(f"\nPaquets manquants: {', '.join(missing_packages)}")
        print("Installez-les avec: pip install -r requirements.txt")
        return False
    
    print("✓ Toutes les dépendances sont installées")
    return True


def check_ollama_connection():
    """Vérifie la connexion à Ollama."""
    try:
        import requests
        response = requests.get('http://100.64.0.34:11434/api/version', timeout=5)
        if response.status_code == 200:
            print("✓ Connexion à Ollama OK")
            return True
        else:
            print("✗ Ollama ne répond pas correctement")
            return False
    except Exception as e:
        print(f"✗ Impossible de se connecter à Ollama: {e}")
        print("Assurez-vous qu'Ollama est démarré avec: ollama serve")
        return False


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Démarre le serveur ChatBot RAG")
    parser.add_argument("--host", default="0.0.0.0", help="Adresse IP du serveur")
    parser.add_argument("--port", type=int, default=8000, help="Port du serveur")
    parser.add_argument("--workers", type=int, default=1, help="Nombre de workers")
    parser.add_argument("--reload", action="store_true", help="Mode développement avec rechargement automatique")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--skip-checks", action="store_true", help="Ignorer les vérifications de dépendances")
    
    args = parser.parse_args()
    
    print("🚀 Démarrage du ChatBot RAG")
    print("=" * 50)
    
    # Configuration du logging
    setup_logging(args.log_level)
    
    # Créer les répertoires nécessaires
    print("\n📁 Création des répertoires...")
    create_directories()
    
    if not args.skip_checks:
        # Vérification des dépendances
        print("\n📦 Vérification des dépendances...")
        if not check_dependencies():
            sys.exit(1)
        
        # Vérification de la connexion Ollama
        print("\n🤖 Vérification d'Ollama...")
        if not check_ollama_connection():
            print("⚠️  Ollama n'est pas accessible. Le serveur démarrera mais les fonctionnalités LLM ne seront pas disponibles.")
    
    # Configuration du serveur
    server_config = {
        "app": app,
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level.lower(),
        "workers": args.workers if not args.reload else 1,
        "reload": args.reload,
        "access_log": True
    }
    
    print(f"\n🌐 Démarrage du serveur sur http://{args.host}:{args.port}")
    print(f"📖 Documentation disponible sur http://{args.host}:{args.port}/docs")
    print(f"🔧 Interface d'administration sur http://{args.host}:{args.port}/api/v1/admin/status")
    
    if args.reload:
        print("🔄 Mode développement activé (rechargement automatique)")
    
    print("\n" + "=" * 50)
    print("Le serveur est prêt! Appuyez sur Ctrl+C pour arrêter.")
    
    try:
        uvicorn.run(**server_config)
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur...")
        print("👋 Au revoir!")


if __name__ == "__main__":
    main() 