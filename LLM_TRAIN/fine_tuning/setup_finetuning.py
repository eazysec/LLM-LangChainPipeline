#!/usr/bin/env python3
"""
🛠️ Setup Automatique : Fine-tuning Mystique
Installation et configuration complète pour le fine-tuning
"""

import subprocess
import sys
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FineTuningSetup:
    """Setup automatique pour le fine-tuning mystique."""
    
    def __init__(self):
        self.requirements = [
            "torch>=2.0.0",
            "transformers>=4.35.0", 
            "peft>=0.6.0",
            "datasets>=2.14.0",
            "accelerate>=0.24.0",
            "sentencepiece>=0.1.99",
            "protobuf>=3.20.0",
            "bitsandbytes>=0.41.0",  # Pour la quantisation
            "scipy>=1.11.0"
        ]
        
        self.base_dir = Path("./fine_tuning")
        self.models_dir = Path("./fine_tuned_models")
        
    def check_system_requirements(self) -> bool:
        """Vérifie les prérequis système."""
        logger.info("🔍 Vérification des prérequis système...")
        
        # Python version
        if sys.version_info < (3, 8):
            logger.error("❌ Python 3.8+ requis")
            return False
        
        # GPU check
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                
                logger.info(f"✅ GPU détecté : {gpu_name}")
                logger.info(f"📊 Mémoire GPU : {gpu_memory:.1f} GB")
                
                if gpu_memory < 4:
                    logger.warning("⚠️ Mémoire GPU < 4GB - fine-tuning sera lent")
            else:
                logger.warning("⚠️ Pas de GPU CUDA - utilisation CPU (très lent)")
        except ImportError:
            logger.warning("⚠️ PyTorch non installé - sera installé")
        
        # Disk space
        disk_space = os.statvfs('.').f_bavail * os.statvfs('.').f_frsize / (1024**3)
        if disk_space < 10:
            logger.error(f"❌ Espace disque insuffisant : {disk_space:.1f} GB (10GB+ requis)")
            return False
        
        logger.info(f"✅ Espace disque : {disk_space:.1f} GB")
        return True
    
    def install_requirements(self) -> bool:
        """Installe les dépendances pour le fine-tuning."""
        logger.info("📦 Installation des dépendances...")
        
        try:
            # Mise à jour pip
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Installation des packages
            for requirement in self.requirements:
                logger.info(f"Installing {requirement}...")
                subprocess.run([sys.executable, "-m", "pip", "install", requirement], 
                             check=True, capture_output=True)
            
            logger.info("✅ Toutes les dépendances installées")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erreur installation : {e}")
            return False
    
    def setup_directories(self):
        """Crée la structure de répertoires."""
        logger.info("📁 Création des répertoires...")
        
        directories = [
            self.base_dir,
            self.models_dir,
            self.base_dir / "datasets",
            self.base_dir / "configs", 
            self.base_dir / "logs",
            self.base_dir / "scripts"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ {directory}")
    
    def create_config_files(self):
        """Crée les fichiers de configuration."""
        logger.info("⚙️ Création des configs...")
        
        # Configuration fine-tuning
        config_content = """# Configuration Fine-tuning Mystique
model:
  base_model: "Qwen/Qwen2.5-1.5B-Instruct"
  output_dir: "./fine_tuned_models/mystical_qwen"
  
lora:
  r: 16
  lora_alpha: 32
  lora_dropout: 0.1
  target_modules: ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

training:
  num_epochs: 3
  batch_size: 4
  gradient_accumulation_steps: 4
  learning_rate: 2e-4
  warmup_steps: 100
  max_length: 1024
  
dataset:
  num_examples: 1000
  train_split: 0.9
  
mystical:
  intensity: 0.9
  style: "hermetic_master"
  language: "fr"
"""
        
        config_path = self.base_dir / "configs" / "mystical_config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        logger.info(f"✅ Config créée : {config_path}")
    
    def test_installation(self) -> bool:
        """Teste l'installation."""
        logger.info("🧪 Test de l'installation...")
        
        try:
            import torch
            import transformers
            import peft
            import datasets
            
            logger.info(f"✅ PyTorch {torch.__version__}")
            logger.info(f"✅ Transformers {transformers.__version__}")
            logger.info(f"✅ PEFT {peft.__version__}")
            logger.info(f"✅ Datasets {datasets.__version__}")
            
            # Test simple de chargement
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct", trust_remote_code=True)
            logger.info("✅ Test chargement tokenizer réussi")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test échoué : {e}")
            return False
    
    def generate_launch_scripts(self):
        """Génère les scripts de lancement."""
        logger.info("📜 Génération des scripts...")
        
        # Script de lancement principal
        launch_script = """#!/usr/bin/env python3
'''Script de lancement du fine-tuning mystique'''

import sys
import asyncio
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent))

from fine_tuning.mystical_fine_tuner import main

if __name__ == "__main__":
    print("🔥 LANCEMENT DU FINE-TUNING MYSTIQUE")
    asyncio.run(main())
"""
        
        script_path = self.base_dir / "scripts" / "launch_finetuning.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(launch_script)
        
        # Rendre exécutable
        os.chmod(script_path, 0o755)
        
        # Script de test rapide
        test_script = """#!/usr/bin/env python3
'''Test rapide du modèle fine-tuné'''

import ollama

def test_mystical_model():
    try:
        # Test avec le modèle mystique
        response = ollama.chat(
            model='mystical-qwen',
            messages=[{'role': 'user', 'content': 'Parle-moi de l\\'alchimie'}]
        )
        
        print("🔮 RÉPONSE DU MODÈLE MYSTIQUE :")
        print("="*50)
        print(response['message']['content'])
        print("="*50)
        
    except Exception as e:
        print(f"❌ Erreur test : {e}")
        print("Vérifiez que le modèle mystical-qwen est bien créé dans Ollama")

if __name__ == "__main__":
    test_mystical_model()
"""
        
        test_path = self.base_dir / "scripts" / "test_mystical_model.py"
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        os.chmod(test_path, 0o755)
        
        logger.info(f"✅ Scripts créés :")
        logger.info(f"  - {script_path}")
        logger.info(f"  - {test_path}")
    
    def setup_complete(self) -> bool:
        """Procédure complète de setup."""
        logger.info("🚀 DÉBUT DU SETUP FINE-TUNING MYSTIQUE")
        logger.info("="*60)
        
        steps = [
            ("Vérification système", self.check_system_requirements),
            ("Installation dépendances", self.install_requirements),
            ("Création répertoires", self.setup_directories),
            ("Configuration", self.create_config_files),
            ("Génération scripts", self.generate_launch_scripts),
            ("Test installation", self.test_installation)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n▶️ {step_name}...")
            
            if step_func == self.setup_directories or step_func == self.create_config_files or step_func == self.generate_launch_scripts:
                step_func()  # Ces fonctions ne retournent pas bool
                continue
                
            if not step_func():
                logger.error(f"❌ Échec : {step_name}")
                return False
            
            logger.info(f"✅ {step_name} terminé")
        
        logger.info("\n🎉 SETUP TERMINÉ AVEC SUCCÈS !")
        logger.info("="*60)
        logger.info("📋 PROCHAINES ÉTAPES :")
        logger.info("1. Lancer : python fine_tuning/scripts/launch_finetuning.py")
        logger.info("2. Attendre la fin du fine-tuning (peut prendre 1-3h)")
        logger.info("3. Tester : python fine_tuning/scripts/test_mystical_model.py")
        logger.info("4. Configurer ton app pour utiliser 'mystical-qwen'")
        
        return True


def main():
    """Point d'entrée principal."""
    setup = FineTuningSetup()
    setup.setup_complete()


if __name__ == "__main__":
    main() 