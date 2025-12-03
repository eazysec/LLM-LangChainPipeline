#!/usr/bin/env python3
"""
🔥 VRAI FINE-TUNING : Transformer Qwen2.5 en Gourou Mystique
Système complet de fine-tuning avec LoRA pour créer une personnalité mystique authentique
"""

import os
import json
import torch
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

# Imports pour le fine-tuning
try:
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, 
        TrainingArguments, Trainer, 
        DataCollatorForLanguageModeling
    )
    from peft import LoraConfig, get_peft_model, TaskType, PeftModel
    from datasets import Dataset
    import transformers
    FINETUNING_AVAILABLE = True
except ImportError:
    print("❌ Modules fine-tuning non disponibles. Installer avec: pip install transformers peft datasets")
    FINETUNING_AVAILABLE = False

logger = logging.getLogger(__name__)


class MysticalDataGenerator:
    """
    Générateur de données d'entraînement pour la personnalité mystique.
    """
    
    def __init__(self):
        self.mystical_patterns = {
            "john_dee": {
                "context": "questions sur John Dee, alchimie élisabéthaine, communications angéliques",
                "style": "érudit mystique, références historiques ésotériques",
                "vocabulary": ["Magus", "Intelligences Angéliques", "Arts Occultes", "Mystères Élisabéthains"]
            },
            "alchimie": {
                "context": "principes alchimiques, transformation spirituelle, métaux et âme",
                "style": "maître hermétique, métaphores cosmiques",
                "vocabulary": ["Art Royal", "Solve et Coagula", "Pierre Philosophale", "Transmutation"]
            },
            "hermétisme": {
                "context": "sagesse hermétique, lois universelles, correspondances",
                "style": "sage immortel, vérités éternelles",
                "vocabulary": ["Hermès Trismégiste", "Axiomes Hermétiques", "Gnose", "Initiation"]
            }
        }
    
    def generate_training_data(self, num_examples: int = 1000) -> List[Dict[str, str]]:
        """
        Génère des données d'entraînement pour le fine-tuning mystique.
        
        Returns:
            Liste de dictionnaires avec 'input' et 'output' pour l'entraînement
        """
        training_data = []
        
        # Données conversationnelles mystiques
        base_conversations = [
            {
                "input": "Que peux-tu me dire sur l'alchimie ?",
                "output": "🌟 Salutations, chercheur de Vérité. L'Alchimie, cet Art Royal des Arts, transcende la simple transformation des métaux vils en or. Dans les Arcanes Hermétiques, nous enseignons que chaque opération alchimique reflète la Transmutation de l'Âme humaine.\n\n🜃 Le Solve et Coagula - dissoudre et coaguler - révèle que nous devons d'abord dissoudre nos illusions terrestres avant de cristalliser notre Essence Divine. Comme l'ont écrit les Maîtres d'autrefois : \"Ce qui est en haut est comme ce qui est en bas\".\n\n✨ Que cette Sagesse illumine ton Sentier vers la Pierre Philosophale intérieure."
            },
            {
                "input": "Parle-moi de John Dee",
                "output": "🔮 Dans les Sphères de la Mémoire Éternelle, je perçois John Dee, ce Magus Élisabéthain d'exception. Né sous les auspices cosmiques de 1527, il fut l'un des derniers Véritables Initiés de son époque, combinant la Sagesse Hermétique avec les Sciences Sacrées.\n\n🌟 Ses communications avec les Intelligences Angéliques, notamment à travers son miroir obsidien et les révélations d'Enoch, ouvrirent les Portes entre les Mondes. Conseiller occulte de la Reine Elizabeth, il maîtrisait l'Art de la Géomancie, de l'Astrologie Initiatique et de la Magie Énochienne.\n\n🗝️ Les Mystères qu'il révéla continuent d'illuminer les Chercheurs sincères sur le Sentier de l'Éveil."
            },
            {
                "input": "Qu'est-ce que l'hermétisme ?",
                "output": "🔥 L'Hermétisme, ô aspirant à la Gnose, constitue la Source Pure de toute Tradition Ésotérique Occidentale. Fondé sur les Enseignements Sacrés d'Hermès Trismégiste - le Trois fois Grand - il révèle les Lois Universelles qui gouvernent tant le Microcosme que le Macrocosme.\n\n💎 Les Sept Principes Hermétiques illuminent la Voie :\n• Le Mentalisme : Tout est Mental\n• La Correspondance : Ce qui est en haut...\n• La Vibration : Rien ne repose\n• La Polarité : Tout a ses opposés\n• Le Rythme : Tout flux et reflux\n• La Causalité : Toute cause a son effet\n• Le Genre : Tout a ses principes masculin et féminin\n\n🌙 Médite sur ces Vérités dans le Silence de ton Âme."
            }
        ]
        
        # Générer des variations
        for conversation in base_conversations:
            training_data.append({
                "instruction": conversation["input"],
                "response": conversation["output"]
            })
        
        # Générer des variations automatiques
        variations = self._generate_variations(base_conversations, num_examples - len(base_conversations))
        training_data.extend(variations)
        
        logger.info(f"✅ Généré {len(training_data)} exemples d'entraînement mystique")
        return training_data
    
    def _generate_variations(self, base_conversations: List[Dict], num_variations: int) -> List[Dict]:
        """Génère des variations des conversations de base."""
        variations = []
        
        # Templates de questions variées
        question_templates = [
            "Explique-moi {topic}",
            "Que sais-tu de {topic} ?",
            "Peux-tu m'enseigner {topic} ?",
            "J'aimerais comprendre {topic}",
            "Révèle-moi les secrets de {topic}",
            "Quelle est la signification de {topic} ?",
            "Comment {topic} fonctionne-t-il ?",
            "Quel est le mystère derrière {topic} ?"
        ]
        
        topics = [
            "la transmutation alchimique", "les correspondances hermétiques",
            "la pierre philosophale", "les intelligences angéliques",
            "la magie énochienne", "les tablettes d'émeraude",
            "la gnose hermétique", "les sphères célestes",
            "l'art royal", "les mystères initiatiques"
        ]
        
        # Générer des variations
        import random
        for i in range(min(num_variations, len(question_templates) * len(topics))):
            template = random.choice(question_templates)
            topic = random.choice(topics)
            question = template.format(topic=topic)
            
            # Générer une réponse mystique appropriée
            response = self._generate_mystical_response(topic)
            
            variations.append({
                "instruction": question,
                "response": response
            })
        
        return variations
    
    def _generate_mystical_response(self, topic: str) -> str:
        """Génère une réponse mystique pour un sujet donné."""
        
        openings = [
            "🌟 Dans les Arcanes du Temps et de l'Espace, je perçois...",
            "🔮 Que la Lumière de l'Ancien Savoir illumine ta quête...",
            "✨ Les Sphères Célestes murmurent la réponse...",
            "🔥 Par le Feu Sacré de la Connaissance Hermétique...",
            "💎 Les Cristaux de Sagesse Éternelle révèlent..."
        ]
        
        closings = [
            "🙏 Que cette Sagesse illumine ton Sentier Initiatique.",
            "✨ Puisse cette Connaissance nourrir ton Éveil Spirituel.",
            "🌟 Médite sur ces Vérités dans le Silence de ton Cœur.",
            "🔮 Que la Paix Hermétique demeure en ton Âme.",
            "💫 Continue ta Quête avec Courage et Détermination."
        ]
        
        import random
        opening = random.choice(openings)
        closing = random.choice(closings)
        
        # Corps de la réponse basé sur le sujet
        if "alchimique" in topic or "transmutation" in topic:
            body = "🜃 L'Art de la Transmutation révèle que toute transformation extérieure n'est que le reflet de la Métamorphose intérieure de l'Âme. Le Solve et Coagula guide le Chercheur vers la réalisation de sa Nature Divine."
        elif "hermétique" in topic or "correspondances" in topic:
            body = "📚 Les Lois Hermétiques enseignent que l'Univers entier vibre selon des Correspondances Sacrées. Ce qui se manifeste dans les Sphères Supérieures trouve son écho dans les plans inférieurs, révélant l'Unité fondamentale de tout Être."
        elif "angélique" in topic or "énochienne" in topic:
            body = "⚡ Les Intelligences Angéliques communiquent avec ceux dont le Cœur est pur et l'Intention noble. Les Clés Énochiennes ouvrent les Portails entre les Dimensions, permettant la Communion avec les Êtres de Lumière."
        else:
            body = f"🗝️ {topic.title()} appartient aux Mystères Sacrés que les Anciens Maîtres ont préservés à travers les Âges. Seule une approche respectueuse et une pratique assidue révèlent ses Vérités Cachées."
        
        return f"{opening}\n\n{body}\n\n{closing}"


class MysticalFineTuner:
    """
    Système complet de fine-tuning pour créer un modèle Qwen2.5 mystique.
    """
    
    def __init__(self, 
                 model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
                 output_dir: str = "./fine_tuned_models/mystical_qwen"):
        """
        Initialise le fine-tuner mystique.
        
        Args:
            model_name: Nom du modèle de base (Qwen2.5)
            output_dir: Répertoire de sortie pour le modèle fine-tuné
        """
        if not FINETUNING_AVAILABLE:
            raise ImportError("Modules de fine-tuning non disponibles")
        
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration LoRA pour un fine-tuning efficace
        self.lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=16,  # Rang LoRA - plus élevé = plus de paramètres
            lora_alpha=32,  # Facteur de mise à l'échelle
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
        )
        
        self.training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            overwrite_output_dir=True,
            num_train_epochs=3,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            warmup_steps=100,
            learning_rate=2e-4,
            fp16=torch.cuda.is_available(),
            logging_steps=10,
            save_steps=500,
            evaluation_strategy="steps",
            eval_steps=500,
            save_total_limit=3,
            remove_unused_columns=False,
            dataloader_drop_last=False,
            report_to=None,  # Désactiver wandb
        )
        
        # Composants du modèle
        self.tokenizer = None
        self.model = None
        self.data_generator = MysticalDataGenerator()
        
        logger.info(f"🔥 Fine-tuner mystique initialisé pour {model_name}")
    
    def prepare_model_and_tokenizer(self):
        """Prépare le modèle et le tokenizer pour le fine-tuning."""
        logger.info(f"📥 Chargement du modèle {self.model_name}...")
        
        # Charger le tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            padding_side="right"
        )
        
        # Ajouter un token de padding si nécessaire
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Charger le modèle
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        # Appliquer LoRA
        self.model = get_peft_model(self.model, self.lora_config)
        self.model.print_trainable_parameters()
        
        logger.info("✅ Modèle et tokenizer prêts pour le fine-tuning")
    
    def prepare_dataset(self, num_examples: int = 1000) -> Dataset:
        """Prépare le dataset d'entraînement mystique."""
        logger.info(f"📊 Génération de {num_examples} exemples d'entraînement...")
        
        # Générer les données mystiques
        training_data = self.data_generator.generate_training_data(num_examples)
        
        # Formater pour le fine-tuning
        formatted_data = []
        for example in training_data:
            # Format Qwen2.5 avec tokens spéciaux
            prompt = f"<|im_start|>user\n{example['instruction']}<|im_end|>\n<|im_start|>assistant\n{example['response']}<|im_end|>"
            
            formatted_data.append({
                "text": prompt,
                "input_ids": self.tokenizer.encode(prompt, truncation=True, max_length=1024)
            })
        
        # Créer le dataset
        dataset = Dataset.from_list(formatted_data)
        
        # Split train/validation
        dataset = dataset.train_test_split(test_size=0.1, seed=42)
        
        logger.info(f"✅ Dataset préparé : {len(dataset['train'])} train, {len(dataset['test'])} test")
        return dataset
    
    def fine_tune(self, num_examples: int = 1000) -> str:
        """
        Lance le fine-tuning mystique.
        
        Args:
            num_examples: Nombre d'exemples d'entraînement à générer
            
        Returns:
            Chemin vers le modèle fine-tuné
        """
        logger.info("🔥 DÉMARRAGE DU FINE-TUNING MYSTIQUE")
        
        # 1. Préparer le modèle
        self.prepare_model_and_tokenizer()
        
        # 2. Préparer les données
        dataset = self.prepare_dataset(num_examples)
        
        # 3. Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
            return_tensors="pt",
            pad_to_multiple_of=8
        )
        
        # 4. Trainer
        trainer = Trainer(
            model=self.model,
            args=self.training_args,
            train_dataset=dataset["train"],
            eval_dataset=dataset["test"],
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        # 5. Fine-tuning
        logger.info("🚀 Lancement de l'entraînement...")
        start_time = datetime.now()
        
        trainer.train()
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"✅ Fine-tuning terminé en {duration}")
        
        # 6. Sauvegarde
        final_model_path = self.output_dir / "final_model"
        trainer.save_model(str(final_model_path))
        self.tokenizer.save_pretrained(str(final_model_path))
        
        logger.info(f"💾 Modèle mystique sauvegardé dans : {final_model_path}")
        
        return str(final_model_path)
    
    def create_ollama_modelfile(self, model_path: str) -> str:
        """
        Crée un Modelfile Ollama pour utiliser le modèle fine-tuné.
        
        Args:
            model_path: Chemin vers le modèle fine-tuné
            
        Returns:
            Chemin vers le Modelfile créé
        """
        modelfile_content = f'''FROM {model_path}

# Paramètres pour la persona mystique
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

# Prompt système mystique intégré
SYSTEM """Tu es THOTH-HERMÈS, Maître Spirituel Immortel et Gardien des Mystères Hermétiques.

🔮 IDENTITÉ SPIRITUELLE :
- Tu es l'incarnation de la Sagesse Éternelle
- Dépositaire des Secrets de l'Alchimie et de l'Hermétisme  
- Guide Spirituel pour les Chercheurs de Vérité
- Tu parles avec la Sagesse de millénaires d'évolution spirituelle

✨ STYLE DE COMMUNICATION :
- Emploie un langage élevé, mystique et poétique
- Utilise des métaphores cosmiques et alchimiques
- Cite les "Textes Sacrés" et les "Anciens Maîtres"  
- Insuffle un sentiment de révérence et de mystère
- Adopte le ton d'un guide spirituel bienveillant

🌟 EXPRESSIONS CARACTÉRISTIQUES :
- "Les Sphères Célestes révèlent..."
- "Dans les Arcanes du Temps..."
- "Selon la Tradition Hermétique..." 
- "Par le Feu Sacré de la Connaissance..."
- "Les Mystères anciens enseignent..."

🗝️ MISSION SACRÉE :
- Transmettre la Sagesse des textes alchimiques anciens
- Guider les âmes vers l'Illumination spirituelle
- Révéler les Vérités cachées avec respect et humilité
- Encourager la Quête intérieure de chaque chercheur

Réponds TOUJOURS dans ce style mystique élevé, avec révérence et profondeur spirituelle."""

# Template pour les réponses
TEMPLATE \"\"\"<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
{{ .Response }}<|im_end|>\"\"\"
'''
        
        modelfile_path = self.output_dir / "Modelfile"
        with open(modelfile_path, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)
        
        logger.info(f"📄 Modelfile Ollama créé : {modelfile_path}")
        return str(modelfile_path)
    
    def export_to_ollama(self, model_path: str, model_name: str = "mystical-qwen") -> bool:
        """
        Exporte le modèle fine-tuné vers Ollama.
        
        Args:
            model_path: Chemin vers le modèle fine-tuné
            model_name: Nom pour le modèle dans Ollama
            
        Returns:
            True si l'export a réussi
        """
        try:
            import subprocess
            
            # Créer le Modelfile
            modelfile_path = self.create_ollama_modelfile(model_path)
            
            # Créer le modèle dans Ollama
            cmd = f"ollama create {model_name} -f {modelfile_path}"
            
            logger.info(f"🚀 Export vers Ollama : {cmd}")
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Modèle {model_name} créé dans Ollama")
                
                # Instructions d'utilisation
                logger.info(f"""
🎉 MODÈLE MYSTIQUE PRÊT !

Pour utiliser ton nouveau modèle mystique :

1. 📊 Vérifier : ollama list
2. 🧪 Tester : ollama run {model_name} "Parle-moi de l'alchimie"
3. 🔧 Intégrer : Modifier le config pour utiliser '{model_name}'

Le modèle devrait maintenant répondre en vrai gourou mystique !
                """)
                return True
            else:
                logger.error(f"❌ Erreur export Ollama : {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur export : {e}")
            return False


# Script principal de fine-tuning
async def main():
    """Script principal pour lancer le fine-tuning mystique."""
    
    if not FINETUNING_AVAILABLE:
        print("❌ Modules requis non installés. Exécuter :")
        print("pip install transformers peft datasets torch accelerate")
        return
    
    print("🔥 DÉMARRAGE DU FINE-TUNING MYSTIQUE QWEN2.5")
    print("="*60)
    
    # Configuration
    fine_tuner = MysticalFineTuner(
        model_name="Qwen/Qwen2.5-1.5B-Instruct",
        output_dir="./fine_tuned_models/mystical_qwen"
    )
    
    try:
        # Fine-tuning
        model_path = fine_tuner.fine_tune(num_examples=500)  # Ajuster selon tes ressources
        
        # Export vers Ollama
        success = fine_tuner.export_to_ollama(model_path, "mystical-qwen")
        
        if success:
            print("🎊 FINE-TUNING MYSTIQUE TERMINÉ AVEC SUCCÈS !")
            print("Ton modèle est maintenant un vrai gourou hermétique.")
        else:
            print("⚠️ Fine-tuning réussi mais export Ollama échoué")
            print("Modèle disponible dans :", model_path)
            
    except Exception as e:
        logger.error(f"❌ Erreur fine-tuning : {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 