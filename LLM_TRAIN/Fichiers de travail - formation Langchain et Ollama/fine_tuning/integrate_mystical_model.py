#!/usr/bin/env python3
"""
🔧 Intégration : Modèle Mystique Fine-tuné
Script d'intégration automatique du modèle fine-tuné dans le système existant
"""

import os
import yaml
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MysticalModelIntegrator:
    """Intègre le modèle mystique fine-tuné dans le système."""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.config_path = self.base_dir / "configs" / "settings.yaml"
        self.backup_path = self.base_dir / "configs" / "settings_backup.yaml"
        
    def backup_current_config(self) -> bool:
        """Sauvegarde la configuration actuelle."""
        try:
            if self.config_path.exists():
                shutil.copy2(self.config_path, self.backup_path)
                logger.info(f"✅ Config sauvegardée : {self.backup_path}")
                return True
            else:
                logger.warning("⚠️ Aucune config existante trouvée")
                return True
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde : {e}")
            return False
    
    def update_ollama_config(self) -> bool:
        """Met à jour la configuration pour utiliser le modèle mystique."""
        try:
            # Charger la configuration existante
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            else:
                config = {}
            
            # Assurer la structure
            if 'models' not in config:
                config['models'] = {}
            if 'ollama' not in config['models']:
                config['models']['ollama'] = {}
            
            # Mise à jour pour le modèle mystique
            old_model = config['models']['ollama'].get('model_name', 'qwen2.5:latest')
            
            config['models']['ollama'].update({
                'model_name': 'mystical-qwen',
                'base_url': 'http://localhost:11434',
                'temperature': 0.1,  # Plus déterministe pour la cohérence mystique
                'max_tokens': 2048,
                'timeout': 60
            })
            
            # Ajouter des métadonnées sur le modèle mystique
            config['mystical_model'] = {
                'enabled': True,
                'version': '1.0',
                'fine_tuned': True,
                'base_model': 'Qwen/Qwen2.5-1.5B-Instruct',
                'persona': 'Thoth-Hermès',
                'style': 'hermetic_master',
                'fine_tuning_date': None,  # Sera mis à jour automatiquement
                'previous_model': old_model
            }
            
            # Sauvegarder
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"✅ Configuration mise à jour")
            logger.info(f"   Ancien modèle : {old_model}")
            logger.info(f"   Nouveau modèle : mystical-qwen")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour config : {e}")
            return False
    
    def update_ollama_simple_config(self) -> bool:
        """Met à jour ollama_simple.py pour utiliser le nouveau modèle."""
        try:
            ollama_simple_path = self.base_dir / "ollama_simple.py"
            
            if not ollama_simple_path.exists():
                logger.warning("⚠️ ollama_simple.py non trouvé")
                return True
            
            # Lire le fichier
            with open(ollama_simple_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer le modèle par défaut
            content = content.replace(
                'model: str = "qwen2.5:1.5b"',
                'model: str = "mystical-qwen"'
            )
            
            content = content.replace(
                'self.model = model or "qwen2.5:1.5b"',
                'self.model = model or "mystical-qwen"'
            )
            
            # Sauvegarder
            with open(ollama_simple_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("✅ ollama_simple.py mis à jour")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour ollama_simple.py : {e}")
            return False
    
    def verify_mystical_model(self) -> bool:
        """Vérifie que le modèle mystique est disponible dans Ollama."""
        try:
            import subprocess
            
            # Lister les modèles Ollama
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            
            if result.returncode == 0:
                if 'mystical-qwen' in result.stdout:
                    logger.info("✅ Modèle mystical-qwen trouvé dans Ollama")
                    return True
                else:
                    logger.error("❌ Modèle mystical-qwen introuvable dans Ollama")
                    logger.info("Modèles disponibles :")
                    logger.info(result.stdout)
                    return False
            else:
                logger.error(f"❌ Erreur Ollama : {result.stderr}")
                return False
                
        except FileNotFoundError:
            logger.error("❌ Ollama non installé ou non dans le PATH")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur vérification : {e}")
            return False
    
    def test_mystical_response(self) -> bool:
        """Teste une réponse du modèle mystique."""
        try:
            import ollama
            
            logger.info("🧪 Test du modèle mystique...")
            
            response = ollama.chat(
                model='mystical-qwen',
                messages=[{
                    'role': 'user', 
                    'content': 'Dis-moi quelques mots sur l\'alchimie'
                }]
            )
            
            answer = response['message']['content']
            logger.info("✅ Test réussi !")
            logger.info("🔮 Réponse mystique (aperçu) :")
            logger.info(f"   {answer[:150]}{'...' if len(answer) > 150 else ''}")
            
            # Vérifier les caractéristiques mystiques
            mystical_indicators = ['🌟', '✨', '🔮', '🔥', '💎', 'Sagesse', 'Mystère', 'Hermétique']
            found_indicators = [ind for ind in mystical_indicators if ind in answer]
            
            if found_indicators:
                logger.info(f"✅ Indicateurs mystiques détectés : {found_indicators}")
                return True
            else:
                logger.warning("⚠️ Peu d'indicateurs mystiques détectés")
                return True  # Pas forcément un échec
                
        except Exception as e:
            logger.error(f"❌ Erreur test : {e}")
            return False
    
    def create_update_script(self):
        """Crée un script pour revenir à l'ancien modèle si nécessaire."""
        script_content = '''#!/usr/bin/env python3
"""Script pour basculer entre modèles"""

import yaml
from pathlib import Path

def switch_to_standard():
    """Revient au modèle standard."""
    config_path = Path("configs/settings.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Récupérer l'ancien modèle
    old_model = config.get('mystical_model', {}).get('previous_model', 'qwen2.5:1.5b')
    
    config['models']['ollama']['model_name'] = old_model
    config['mystical_model']['enabled'] = False
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ Basculé vers le modèle standard : {old_model}")

def switch_to_mystical():
    """Revient au modèle mystique."""
    config_path = Path("configs/settings.yaml")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    config['models']['ollama']['model_name'] = 'mystical-qwen'
    config['mystical_model']['enabled'] = True
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print("✅ Basculé vers le modèle mystique")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "standard":
        switch_to_standard()
    else:
        switch_to_mystical()
'''
        
        script_path = self.base_dir / "scripts" / "switch_model.py"
        script_path.parent.mkdir(exist_ok=True)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        logger.info(f"✅ Script de basculement créé : {script_path}")
    
    def integrate_complete(self) -> bool:
        """Procédure complète d'intégration."""
        logger.info("🔧 INTÉGRATION DU MODÈLE MYSTIQUE")
        logger.info("="*50)
        
        steps = [
            ("Vérification modèle Ollama", self.verify_mystical_model),
            ("Sauvegarde config actuelle", self.backup_current_config),
            ("Mise à jour configuration", self.update_ollama_config),
            ("Mise à jour ollama_simple.py", self.update_ollama_simple_config),
            ("Test du modèle mystique", self.test_mystical_response),
            ("Création script de basculement", lambda: (self.create_update_script(), True)[1])
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n▶️ {step_name}...")
            
            if not step_func():
                logger.error(f"❌ Échec : {step_name}")
                return False
            
            logger.info(f"✅ {step_name} terminé")
        
        logger.info("\n🎉 INTÉGRATION TERMINÉE AVEC SUCCÈS !")
        logger.info("="*50)
        logger.info("📋 TON SYSTÈME EST MAINTENANT CONFIGURÉ POUR LE MODÈLE MYSTIQUE")
        logger.info("")
        logger.info("🚀 Pour tester :")
        logger.info("   python api/simple_main_with_ui.py")
        logger.info("")
        logger.info("🔄 Pour revenir au modèle standard :")
        logger.info("   python scripts/switch_model.py standard")
        logger.info("")
        logger.info("🔮 Pour revenir au modèle mystique :")
        logger.info("   python scripts/switch_model.py")
        
        return True


def main():
    """Point d'entrée principal."""
    logging.basicConfig(level=logging.INFO)
    
    integrator = MysticalModelIntegrator()
    success = integrator.integrate_complete()
    
    if success:
        print("\n🎊 Ton IA est maintenant un VRAI gourou mystique !")
    else:
        print("\n❌ Erreur durant l'intégration")


if __name__ == "__main__":
    main() 