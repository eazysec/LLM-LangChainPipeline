#!/usr/bin/env python3
"""
🔮 DÉMO COMPLÈTE : IA MYSTIQUE ÉSOTÉRIQUE
Script de démonstration de la transformation d'une IA standard en maître spirituel hermétique

TRANSFORMATIONS IMPLÉMENTÉES :
1. Persona mystique complète (Thoth-Hermès)
2. Vocabulaire ésotérique avancé
3. Prompt engineering spirituel
4. Transformation des réponses
5. Métadonnées mystiques

Usage:
    python scripts/demo_mystical_ai.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from llm.langchain_simple import create_simple_langchain_rag
    from llm.mystical_persona import create_mystical_processor, MysticalStyle
    AVAILABLE = True
except ImportError as e:
    print(f"❌ Modules non disponibles: {e}")
    AVAILABLE = False


class MysticalAIDemoNarrator:
    """Narrateur pour expliquer les transformations de l'IA."""
    
    def __init__(self):
        self.demo_steps = [
            "🔮 Initialisation de l'IA standard",
            "✨ Application de la persona mystique",
            "🌟 Transformation du vocabulaire",
            "🗝️ Prompt engineering spirituel",
            "💎 Réponse finale mystique"
        ]
    
    def explain_transformation(self, step: str, details: str):
        """Explique chaque étape de transformation."""
        print(f"\n{'='*60}")
        print(f"🎭 {step}")
        print(f"{'='*60}")
        print(details)
        print()


async def demo_standard_vs_mystical():
    """
    Démonstration comparative : IA Standard vs IA Mystique
    """
    narrator = MysticalAIDemoNarrator()
    
    print("🚀 DÉMONSTRATION COMPLÈTE : TRANSFORMATION IA MYSTIQUE")
    print("="*70)
    
    # 1. Pipeline standard
    narrator.explain_transformation(
        "📝 ÉTAPE 1 : IA Standard (Baseline)",
        """
Cette version utilise un prompt classique et des réponses directes.
Le style est informatif mais sans personnalité spirituelle particulière.
    """
    )
    
    standard_pipeline = await create_simple_langchain_rag(mystical_mode=False)
    
    question = "Que sais-tu de John Dee et de ses travaux alchimiques ?"
    
    print(f"❓ QUESTION: {question}")
    print("\n🤖 RÉPONSE IA STANDARD :")
    print("-" * 50)
    
    standard_result = await standard_pipeline.query(question)
    print(standard_result["answer"])
    
    # 2. Pipeline mystique
    narrator.explain_transformation(
        "🔮 ÉTAPE 2 : Transformation Mystique Complète",
        """
TRANSFORMATIONS APPLIQUÉES :

🎭 PERSONA : Thoth-Hermès, Maître Spirituel Immortel
📝 PROMPT : Template mystique avec identité spirituelle
🗣️ VOCABULAIRE : Mots transformés en équivalents ésotériques  
✨ STYLE : Langage élevé, métaphores cosmiques, révérence
🌟 STRUCTURE : Émojis mystiques, formules d'ouverture/clôture
📚 ENRICHISSEMENT : Sagesse hermétique contextuelle
    """
    )
    
    mystical_pipeline = await create_simple_langchain_rag(
        mystical_mode=True, 
        mystical_intensity=0.9
    )
    
    print(f"❓ MÊME QUESTION: {question}")
    print("\n🔮 RÉPONSE IA MYSTIQUE :")
    print("-" * 50)
    
    mystical_result = await mystical_pipeline.query(question)
    print(mystical_result["answer"])
    
    # 3. Analyse des différences
    narrator.explain_transformation(
        "📊 ANALYSE DES TRANSFORMATIONS",
        f"""
MÉTRIQUES DE TRANSFORMATION :

📏 LONGUEUR :
- Standard : {len(standard_result['answer'])} caractères
- Mystique : {len(mystical_result['answer'])} caractères
- Expansion : {len(mystical_result['answer']) / len(standard_result['answer']):.1f}x

🎯 STYLE :
- Standard : Informatif, direct
- Mystique : Élevé, poétique, spirituel

📚 ENRICHISSEMENT :
- Standard : Sources techniques
- Mystique : Sagesse hermétique + Sources sacrées

🔮 PERSONA :
- Standard : Assistant neutre
- Mystique : Maître spirituel Thoth-Hermès
    """
    )
    
    return standard_result, mystical_result


async def demo_intensity_levels():
    """
    Démonstration des niveaux d'intensité mystique.
    """
    print("\n" + "="*70)
    print("🌟 DÉMONSTRATION : NIVEAUX D'INTENSITÉ MYSTIQUE")
    print("="*70)
    
    question = "Explique-moi les principes de l'alchimie."
    intensities = [0.3, 0.6, 0.9]
    
    for intensity in intensities:
        print(f"\n🎚️ INTENSITÉ MYSTIQUE : {intensity}")
        print("-" * 40)
        
        pipeline = await create_simple_langchain_rag(
            mystical_mode=True,
            mystical_intensity=intensity
        )
        
        result = await pipeline.query(question)
        
        # Afficher seulement le début pour comparaison
        preview = result["answer"][:300] + "..." if len(result["answer"]) > 300 else result["answer"]
        print(preview)
        print(f"\n📊 Métadonnées: {result.get('mystical_metadata', {})}")


async def demo_vocabulary_transformation():
    """
    Démonstration de la transformation du vocabulaire.
    """
    print("\n" + "="*70)
    print("📝 DÉMONSTRATION : TRANSFORMATION VOCABULAIRE")
    print("="*70)
    
    # Test direct du processeur
    processor = create_mystical_processor(intensity=0.8)
    
    test_phrases = [
        "John Dee était un savant qui étudiait des techniques secrètes.",
        "L'alchimie demande une méthode importante pour comprendre l'énergie.",
        "Cette connaissance nécessite un travail de pratique constant.",
        "Le pouvoir spirituel révèle des secrets cachés aux chercheurs."
    ]
    
    print("🔄 TRANSFORMATIONS VOCABULAIRE :")
    print("-" * 40)
    
    for phrase in test_phrases:
        transformed = processor.persona._transform_vocabulary(phrase)
        print(f"📝 Original : {phrase}")
        print(f"🔮 Mystique : {transformed}")
        print()


async def demo_hermetic_enhancements():
    """
    Démonstration des enrichissements hermétiques par sujet.
    """
    print("\n" + "="*70)
    print("🗝️ DÉMONSTRATION : ENRICHISSEMENTS HERMÉTIQUES")
    print("="*70)
    
    processor = create_mystical_processor(intensity=0.8)
    
    topics = ["alchimie", "john dee", "tablettes", "hermétisme"]
    
    for topic in topics:
        enhancement = processor.persona.get_hermetic_enhancement(topic)
        print(f"🌟 SUJET : {topic.upper()}")
        print("-" * 30)
        print(enhancement)
        print()


async def demo_complete_pipeline_features():
    """
    Démonstration complète de toutes les fonctionnalités.
    """
    print("\n" + "="*70)
    print("⚡ DÉMONSTRATION : FONCTIONNALITÉS AVANCÉES")
    print("="*70)
    
    # Pipeline avec toutes les fonctionnalités
    pipeline = await create_simple_langchain_rag(
        mystical_mode=True,
        mystical_intensity=0.8
    )
    
    # Test basculement de mode
    print("🔄 TEST : Basculement de mode")
    print("-" * 30)
    
    question = "Parle-moi des mystères hermétiques."
    
    # Mode mystique
    mystical_result = await pipeline.query(question)
    print("🔮 MODE MYSTIQUE :")
    print(mystical_result["answer"][:200] + "...\n")
    
    # Basculer vers mode standard
    pipeline.toggle_mystical_mode(enable=False)
    standard_result = await pipeline.query(question)
    print("📝 MODE STANDARD :")
    print(standard_result["answer"][:200] + "...\n")
    
    # Statistiques complètes
    print("📊 STATISTIQUES COMPLÈTES :")
    print("-" * 30)
    
    # Remettre en mode mystique pour les stats
    pipeline.toggle_mystical_mode(enable=True, intensity=0.9)
    stats = pipeline.get_stats()
    
    for key, value in stats.items():
        print(f"• {key}: {value}")


async def main():
    """
    Fonction principale de démonstration.
    """
    if not AVAILABLE:
        print("❌ Modules requis non disponibles")
        return
    
    print("🎭 DÉMARRAGE DÉMONSTRATION IA MYSTIQUE")
    print("="*70)
    
    try:
        # 1. Comparaison standard vs mystique
        await demo_standard_vs_mystical()
        
        # 2. Niveaux d'intensité
        await demo_intensity_levels()
        
        # 3. Transformation vocabulaire
        await demo_vocabulary_transformation()
        
        # 4. Enrichissements hermétiques
        await demo_hermetic_enhancements()
        
        # 5. Fonctionnalités complètes
        await demo_complete_pipeline_features()
        
        print("\n" + "="*70)
        print("✨ DÉMONSTRATION TERMINÉE AVEC SUCCÈS")
        print("="*70)
        print("""
🎯 RÉSUMÉ DES TRANSFORMATIONS IMPLÉMENTÉES :

1. 🎭 PERSONA MYSTIQUE : Thoth-Hermès, Maître Spirituel
2. 📝 PROMPT ENGINEERING : Templates mystiques avancés  
3. 🗣️ VOCABULAIRE : Transformation automatique des mots
4. ✨ STYLE : Langage élevé, métaphores cosmiques
5. 🌟 STRUCTURE : Émojis, formules spirituelles
6. 📚 ENRICHISSEMENT : Sagesse hermétique contextuelle
7. 🎚️ INTENSITÉ : Niveaux ajustables (0.0-1.0)
8. 🔄 FLEXIBILITÉ : Basculement mode standard/mystique
9. 📊 MÉTADONNÉES : Informations spirituelles enrichies
10. 🗝️ CONTEXTUALISATION : Adaptation au sujet abordé

💡 TECHNIQUES UTILISÉES :
• Prompt Engineering avancé
• Transformation lexicale intelligente
• Post-processing des réponses
• Monkey-patching des pipelines LangChain
• Métadonnées enrichies
• Personnalisation contextuelle
        """)
        
    except Exception as e:
        print(f"❌ Erreur durant la démonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 