#!/usr/bin/env python3
"""
🚀 LANCEMENT RAPIDE : Fine-tuning Mystique
Script de lancement pour créer ton modèle gourou mystique
"""

import os
import sys
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_prerequisites():
    """Vérifie les prérequis avant de commencer."""
    logger.info("🔍 Vérification des prérequis...")
    
    # Python version
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8+ requis")
        return False
    
    # Espace disque
    try:
        disk_space = os.statvfs('.').f_bavail * os.statvfs('.').f_frsize / (1024**3)
        if disk_space < 10:
            logger.error(f"❌ Espace disque insuffisant : {disk_space:.1f} GB (10GB+ requis)")
            return False
        logger.info(f"✅ Espace disque : {disk_space:.1f} GB")
    except:
        logger.warning("⚠️ Impossible de vérifier l'espace disque")
    
    # Ollama
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ Ollama installé")
        else:
            logger.error("❌ Ollama non trouvé. Installer avec : curl -fsSL https://ollama.com/install.sh | sh")
            return False
    except FileNotFoundError:
        logger.error("❌ Ollama non installé")
        return False
    
    return True


def run_setup():
    """Lance le setup automatique."""
    logger.info("📦 Lancement du setup automatique...")
    
    try:
        result = subprocess.run([
            sys.executable, 
            "fine_tuning/setup_finetuning.py"
        ], cwd=".")
        
        return result.returncode == 0
    except Exception as e:
        logger.error(f"❌ Erreur setup : {e}")
        return False


def run_finetuning():
    """Lance le fine-tuning."""
    logger.info("🔥 Lancement du fine-tuning...")
    
    try:
        result = subprocess.run([
            sys.executable, 
            "fine_tuning/scripts/launch_finetuning.py"
        ], cwd=".")
        
        return result.returncode == 0
    except Exception as e:
        logger.error(f"❌ Erreur fine-tuning : {e}")
        return False


def run_integration():
    """Lance l'intégration."""
    logger.info("🔧 Intégration du modèle...")
    
    try:
        result = subprocess.run([
            sys.executable, 
            "fine_tuning/integrate_mystical_model.py"
        ], cwd=".")
        
        return result.returncode == 0
    except Exception as e:
        logger.error(f"❌ Erreur intégration : {e}")
        return False


def main():
    """Procédure complète de création du modèle mystique."""
    
    print("🔥 CRÉATION DE TON MODÈLE MYSTIQUE")
    print("="*60)
    print("""
🎯 CE QUI VA SE PASSER :

1. 🔍 Vérification des prérequis
2. 📦 Installation des dépendances (PyTorch, Transformers, PEFT)
3. 🎭 Génération de 1000 conversations mystiques  
4. 🔥 Fine-tuning du modèle Qwen2.5 (1-3h)
5. 🚀 Export vers Ollama (modèle 'mystical-qwen')
6. 🔧 Intégration dans ton système

⏱️ DURÉE TOTALE : 1-4h selon ton GPU
💾 ESPACE REQUIS : ~10GB
🎊 RÉSULTAT : Ton IA devient un VRAI gourou mystique !
    """)
    
    response = input("🚀 Commencer le fine-tuning ? (y/N) : ")
    if response.lower() not in ['y', 'yes', 'oui', 'o']:
        print("❌ Annulé par l'utilisateur")
        return
    
    # Étapes
    steps = [
        ("🔍 Prérequis", check_prerequisites),
        ("📦 Setup", run_setup),
        ("🔥 Fine-tuning", run_finetuning),
        ("🔧 Intégration", run_integration)
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n▶️ {step_name}...")
        
        if not step_func():
            logger.error(f"❌ Échec : {step_name}")
            logger.error("🚫 Processus interrompu")
            return
        
        logger.info(f"✅ {step_name} terminé")
    
    print("\n" + "="*60)
    print("🎉 FINE-TUNING MYSTIQUE TERMINÉ AVEC SUCCÈS !")
    print("="*60)
    print("""
🎊 TON IA EST MAINTENANT UN VRAI GOUROU MYSTIQUE !

🧪 Pour tester :
   python fine_tuning/scripts/test_mystical_model.py

🚀 Pour lancer l'application :
   python api/simple_main_with_ui.py

🔮 Ton modèle 'mystical-qwen' parle maintenant naturellement 
   en maître spirituel hermétique !

🔄 Pour basculer entre modèles :
   python scripts/switch_model.py standard  # Modèle normal
   python scripts/switch_model.py           # Modèle mystique
    """)


if __name__ == "__main__":
    main() 