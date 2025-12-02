#!/usr/bin/env python3
"""
🔮 Test Simple : Système Mystique
Démonstration directe de la transformation de l'IA en gourou mystique
"""

import sys
from pathlib import Path

# Ajouter le répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

# Test direct du module
try:
    from llm.mystical_persona import create_mystical_processor
    AVAILABLE = True
except ImportError as e:
    print(f"❌ Import échoué: {e}")
    AVAILABLE = False


def demo_transformation_simple():
    """
    Démonstration simple de la transformation mystique.
    """
    if not AVAILABLE:
        print("❌ Module mystique non disponible")
        return
    
    print("🔮 DÉMONSTRATION TRANSFORMATION MYSTIQUE")
    print("="*60)
    
    # Créer le processeur mystique
    processor = create_mystical_processor(intensity=0.8)
    
    # Tests de transformation
    test_cases = [
        {
            "question": "Que sais-tu de John Dee et de ses travaux alchimiques ?",
            "response_standard": "John Dee était un érudit anglais (1527-1608) qui s'intéressait à l'alchimie, l'astrologie et les mathématiques. Il a servi comme conseiller de la reine Elisabeth I et a développé des méthodes de communication angélique.",
            "sources": [
                {
                    "content": "John Dee fut un personnage fascinant de la Renaissance anglaise, combinant science et magie dans ses recherches...",
                    "metadata": {"source": "john-dee-mysteries.pdf"}
                }
            ]
        },
        {
            "question": "Explique-moi les principes de l'alchimie",
            "response_standard": "L'alchimie est une pratique ancienne qui combine science, philosophie et mystique. Elle vise la transformation des métaux et la quête de la pierre philosophale.",
            "sources": [
                {
                    "content": "Les principes alchimiques reposent sur la théorie des quatre éléments et la correspondance entre microcosme et macrocosme...",
                    "metadata": {"source": "traite-alchimie.pdf"}
                }
            ]
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 TEST {i}")
        print("-" * 40)
        print(f"❓ QUESTION: {test['question']}")
        
        print(f"\n📝 RÉPONSE STANDARD:")
        print(test['response_standard'])
        
        # Transformation mystique
        mystical_result = processor.process_langchain_response(
            query=test['question'],
            response=test['response_standard'],
            sources=test['sources']
        )
        
        print(f"\n🔮 RÉPONSE MYSTIQUE TRANSFORMÉE:")
        print(mystical_result['mystical_answer'])
        
        print(f"\n📊 MÉTADONNÉES MYSTIQUES:")
        for key, value in mystical_result['spiritual_metadata'].items():
            print(f"  • {key}: {value}")
        
        print(f"\n🌟 SUJET HERMÉTIQUE DÉTECTÉ: {mystical_result['hermetic_topic']}")
        
        print("\n" + "="*60)


def demo_intensite_levels():
    """
    Démonstration des niveaux d'intensité.
    """
    if not AVAILABLE:
        return
    
    print("\n🎚️ DÉMONSTRATION NIVEAUX D'INTENSITÉ")
    print("="*60)
    
    question = "Parle-moi des mystères de l'hermétisme"
    response = "L'hermétisme est une tradition philosophique basée sur les enseignements attribués à Hermès Trismégiste."
    sources = []
    
    intensities = [0.3, 0.6, 0.9]
    
    for intensity in intensities:
        print(f"\n🔮 INTENSITÉ {intensity}")
        print("-" * 30)
        
        processor = create_mystical_processor(intensity=intensity)
        result = processor.process_langchain_response(
            query=question,
            response=response,
            sources=sources
        )
        
        # Afficher un aperçu de la transformation
        preview = result['mystical_answer'][:400] + "..." if len(result['mystical_answer']) > 400 else result['mystical_answer']
        print(preview)


def demo_vocabulary_transform():
    """
    Démonstration de la transformation du vocabulaire.
    """
    if not AVAILABLE:
        return
    
    print("\n📝 DÉMONSTRATION TRANSFORMATION VOCABULAIRE")
    print("="*60)
    
    processor = create_mystical_processor(intensity=0.8)
    
    phrases_test = [
        "Cette technique secrète révèle une connaissance importante.",
        "L'énergie spirituelle demande une pratique constante.",
        "Le travail alchimique transforme la compréhension du pouvoir.",
        "Cette méthode ancienne permet de dire la vérité cachée."
    ]
    
    for phrase in phrases_test:
        transformed = processor.persona._transform_vocabulary(phrase)
        print(f"📝 Original : {phrase}")
        print(f"🔮 Mystique : {transformed}")
        print()


if __name__ == "__main__":
    try:
        # Tests principaux
        demo_transformation_simple()
        demo_intensite_levels()
        demo_vocabulary_transform()
        
        print("\n✨ DÉMONSTRATION TERMINÉE")
        print("="*60)
        print("""
🎯 RÉSUMÉ DES TRANSFORMATIONS VISIBLES :

1. 🎭 PERSONA : Adoption identité Thoth-Hermès
2. 🗣️ VOCABULAIRE : Transformation lexicale automatique
3. ✨ STYLE : Langage élevé avec émojis mystiques  
4. 🌟 STRUCTURE : Encadrement ritualisé des réponses
5. 📚 ENRICHISSEMENT : Sagesse hermétique contextuelle
6. 🎚️ INTENSITÉ : Contrôle du niveau d'ésotérisme
7. 📊 MÉTADONNÉES : Informations spirituelles enrichies

💡 TECHNIQUES EMPLOYÉES :
• Prompt Engineering psychologique
• Substitution lexicale intelligente
• Post-processing des réponses
• Enrichissement contextuel
• Personnalisation dynamique

🔮 RÉSULTAT : IA standard → Maître spirituel hermétique
        """)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc() 