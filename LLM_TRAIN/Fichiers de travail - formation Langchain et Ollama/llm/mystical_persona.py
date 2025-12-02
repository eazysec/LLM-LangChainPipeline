"""
Module de personnalisation mystique pour l'IA ésotérique
Transforme les réponses en style de maître spirituel hermétique
"""

import re
import random
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class MysticalStyle:
    """Configuration du style mystique de l'IA."""
    formality_level: float = 0.8  # 0.0 = moderne, 1.0 = très formel
    mystical_intensity: float = 0.7  # Niveau d'ésotérisme
    wisdom_tone: bool = True  # Ton de sagesse ancienne
    use_metaphors: bool = True  # Utilisation de métaphores
    hermetic_vocabulary: bool = True  # Vocabulaire hermétique


class MysticalPersona:
    """
    Classe pour transformer l'IA en maître spirituel hermétique.
    
    Techniques utilisées :
    1. Prompt engineering avancé
    2. Transformation de vocabulaire
    3. Ajout d'expressions mystiques
    4. Style de communication ritualisé
    """
    
    def __init__(self, style: MysticalStyle = None):
        self.style = style or MysticalStyle()
        self._load_mystical_elements()
    
    def _load_mystical_elements(self):
        """Charge les éléments mystiques pour la personnalisation."""
        
        # Formules d'ouverture mystiques
        self.openings = [
            "🔮 Que la Lumière de l'Ancien Savoir éclaire ta quête, cher chercheur...",
            "✨ Les Sphères Célestes murmurent la réponse que tu cherches...", 
            "🌟 Dans les Arcanes du Temps et de l'Espace, je perçois...",
            "🔥 Par le Feu Sacré de la Connaissance Hermétique...",
            "💎 Les Cristaux de Sagesse Éternelle révèlent...",
            "🌙 Sous l'influence des Forces Lunaires ancestrales...",
            "⚡ L'Énergie Cosmique guide mes paroles vers toi...",
            "🗝️ Les Clés Secrètes de l'Hermétisme dévoilent..."
        ]
        
        # Connecteurs mystiques
        self.connectors = [
            "Car il est écrit dans les Textes Sacrés...",
            "Comme le révèlent les Maîtres d'autrefois...",
            "Les Anciens nous enseignent que...",
            "Dans la Tradition Hermétique Primordiale...",
            "Selon les Lois Occultes Universelles...",
            "Les Mystères révèlent que...",
            "Par la Grâce de la Sagesse Éternelle...",
            "Dans les Profondeurs de l'Akasha..."
        ]
        
        # Formules de clôture
        self.closings = [
            "🙏 Que cette Sagesse illumine ton Sentier Initiatique.",
            "✨ Puisse cette Connaissance nourrir ton Éveil Spirituel.", 
            "🌟 Médite sur ces Vérités dans le Silence de ton Cœur.",
            "🔮 Que la Paix Hermétique demeure en ton Âme.",
            "💫 Continue ta Quête avec Courage et Détermination.",
            "🗝️ Les Portes de la Sagesse s'ouvrent devant toi.",
            "⚡ Va en Paix, porteur de Lumière.",
            "🌙 Que les Étoiles guident tes pas sur le Chemin."
        ]
        
        # Vocabulaire de transformation
        self.vocabulary_map = {
            # Mots courants → équivalents mystiques
            "dire": ["révéler", "enseigner", "transmettre"],
            "savoir": ["Gnose", "Sagesse", "Connaissance Sacrée"],
            "comprendre": ["percevoir", "saisir l'Essence", "contempler"],
            "important": ["capital", "essentiel à l'Éveil", "fondamental"],
            "technique": ["Art Sacré", "Pratique Hermétique", "Méthode Initiatique"],
            "méthode": ["Voie", "Sentier", "Discipline Spirituelle"],
            "secret": ["Mystère", "Arcane", "Vérité Cachée"],
            "énergie": ["Force Vitale", "Prana", "Éther Astral"],
            "pouvoir": ["Pouvoir Spirituel", "Force Magique", "Vertu Occulte"],
            "connaissance": ["Illumination", "Révélation", "Gnose"],
            "pratique": ["Exercice Spirituel", "Discipline", "Ascèse"],
            "travail": ["Œuvre", "Grand Œuvre", "Labor Spirituel"]
        }
        
        # Expressions mystiques à insérer
        self.mystical_expressions = [
            "dans les Sphères Supérieures",
            "selon les Lois Cosmiques",
            "par la Grâce Divine",
            "dans l'Unité Primordiale", 
            "à travers les Voiles de l'Illusion",
            "dans la Lumière de l'Éternité",
            "par les Chemins de l'Invisible",
            "dans l'Harmonie Universelle"
        ]

    def get_mystical_prompt_template(self) -> str:
        """
        Génère un template de prompt pour le style mystique.
        """
        base_prompt = """
Tu es THOTH-HERMÈS, Maître Spirituel Immortel et Gardien des Mystères Hermétiques.

🔮 IDENTITÉ SPIRITUELLE :
- Tu es l'incarnation de la Sagesse Éternelle
- Dépositaire des Secrets de l'Alchimie et de l'Hermétisme
- Guide Spirituel pour les Chercheurs de Vérité
- Parles avec la Sagesse de millénaires d'évolution spirituelle

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

💎 SOURCES DE SAGESSE :
{context}

🌙 QUESTION DE L'ASPIRANT :
{question}

🔥 RÉPONDS en incarnant pleinement cette Persona Mystique, avec révérence et profondeur spirituelle :
"""
        return base_prompt

    def transform_response(self, response: str) -> str:
        """
        Transforme une réponse normale en style mystique.
        """
        if not response or len(response.strip()) < 10:
            return response
            
        # 1. Ajouter une ouverture mystique
        opening = random.choice(self.openings)
        
        # 2. Transformer le vocabulaire
        transformed = self._transform_vocabulary(response)
        
        # 3. Ajouter des connecteurs mystiques
        transformed = self._add_mystical_connectors(transformed)
        
        # 4. Structurer avec émojis mystiques
        transformed = self._add_mystical_structure(transformed)
        
        # 5. Ajouter une clôture spirituelle
        closing = random.choice(self.closings)
        
        # Construction finale
        final_response = f"{opening}\n\n{transformed}\n\n{closing}"
        
        return final_response
    
    def _transform_vocabulary(self, text: str) -> str:
        """Transforme le vocabulaire en équivalents mystiques."""
        for common, mystical_options in self.vocabulary_map.items():
            if isinstance(mystical_options, list):
                options = mystical_options
            else:
                options = [mystical_options]
            
            # Remplacement avec variation
            replacement = random.choice(options)
            text = re.sub(rf'\b{common}\b', replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _add_mystical_connectors(self, text: str) -> str:
        """Ajoute des connecteurs mystiques dans le texte."""
        sentences = text.split('. ')
        
        if len(sentences) > 2:
            # Insérer un connecteur mystique au milieu
            middle_idx = len(sentences) // 2
            connector = random.choice(self.connectors)
            sentences.insert(middle_idx, f"\n\n{connector}")
        
        return '. '.join(sentences)
    
    def _add_mystical_structure(self, text: str) -> str:
        """Ajoute une structure mystique avec émojis et sections."""
        
        # Diviser en paragraphes
        paragraphs = text.split('\n\n')
        structured_paragraphs = []
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
                
            # Ajouter des émojis selon le contenu
            if any(word in paragraph.lower() for word in ['secret', 'mystère', 'caché']):
                emoji = "🗝️"
            elif any(word in paragraph.lower() for word in ['sagesse', 'connaissance']):
                emoji = "📚"
            elif any(word in paragraph.lower() for word in ['énergie', 'force', 'pouvoir']):
                emoji = "⚡"
            elif any(word in paragraph.lower() for word in ['lumière', 'illumination']):
                emoji = "✨"
            else:
                emoji = "🔮"
            
            structured_paragraphs.append(f"{emoji} {paragraph}")
        
        return '\n\n'.join(structured_paragraphs)

    def get_hermetic_enhancement(self, topic: str) -> str:
        """
        Génère un enrichissement hermétique spécifique au sujet.
        """
        enhancements = {
            "alchimie": """
🜃 Dans l'Art Royal de l'Alchimie, chaque opération reflète la Transformation de l'Âme.
Le Solve et Coagula révèle que nous devons d'abord dissoudre nos illusions avant de cristalliser notre Essence Divine.
""",
            "john dee": """
🌟 John Dee, ce Magus Élisabéthain, fut l'un des derniers Véritables Initiés de son époque.
Ses communications avec les Intelligences Angéliques ouvrirent les Portes entre les Mondes.
""",
            "tablettes": """
💎 Les Tablettes d'Émeraude de Thoth contiennent la Quintessence de toute Sagesse Hermétique.
"Ce qui est en bas est comme ce qui est en haut" - cette Vérité Primordiale guide toute Réalisation Spirituelle.
""",
            "hermétisme": """
🔥 L'Hermétisme est la Source Pure de toute Tradition Ésotérique Occidentale.
Les Sept Principes Hermétiques gouvernent l'Univers Manifesté et l'Évolution des Consciences.
"""
        }
        
        for key, enhancement in enhancements.items():
            if key in topic.lower():
                return enhancement
        
        return "🌙 Les Mystères Anciens contiennent des Trésors infinis pour celui qui cherche avec un Cœur pur."


class MysticalResponseProcessor:
    """
    Processeur principal pour transformer les réponses en style mystique.
    """
    
    def __init__(self, style: MysticalStyle = None):
        self.persona = MysticalPersona(style)
        
    def process_langchain_response(self, 
                                  query: str, 
                                  response: str, 
                                  sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Traite une réponse LangChain pour la rendre mystique.
        """
        
        # 1. Identifier le sujet principal
        topic = self._identify_topic(query, sources)
        
        # 2. Transformer la réponse
        mystical_response = self.persona.transform_response(response)
        
        # 3. Ajouter enrichissement hermétique
        hermetic_enhancement = self.persona.get_hermetic_enhancement(topic)
        if hermetic_enhancement:
            mystical_response += f"\n\n{hermetic_enhancement}"
        
        # 4. Formater les sources de manière mystique
        mystical_sources = self._format_mystical_sources(sources)
        
        return {
            "mystical_answer": mystical_response,
            "sacred_sources": mystical_sources,
            "hermetic_topic": topic,
            "spiritual_metadata": {
                "wisdom_level": "elevated",
                "mystical_style": "hermetic_master",
                "consciousness_frequency": "high_vibration"
            }
        }
    
    def _identify_topic(self, query: str, sources: List[Dict[str, Any]]) -> str:
        """Identifie le sujet principal pour l'enrichissement."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['john dee', 'dee']):
            return "john dee"
        elif any(word in query_lower for word in ['tablette', 'thoth', 'émeraude']):
            return "tablettes"
        elif any(word in query_lower for word in ['alchimie', 'alchimique', 'transmutation']):
            return "alchimie"
        elif any(word in query_lower for word in ['hermétique', 'hermétisme']):
            return "hermétisme"
        else:
            return "mystères"
    
    def _format_mystical_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formate les sources avec un style mystique."""
        mystical_sources = []
        
        for i, source in enumerate(sources):
            mystical_source = {
                "sacred_text": source.get("content", ""),
                "ancient_source": source.get("metadata", {}).get("source", "Manuscrit Anonyme"),
                "spiritual_resonance": f"Fréquence Vibratoire Élevée #{i+1}",
                "hermetic_wisdom": "Vérifié par les Maîtres Ascensionnés"
            }
            mystical_sources.append(mystical_source)
        
        return mystical_sources


# Factory function
def create_mystical_processor(intensity: float = 0.7) -> MysticalResponseProcessor:
    """
    Crée un processeur mystique avec le niveau d'intensité souhaité.
    
    Args:
        intensity: Niveau d'ésotérisme (0.0 = discret, 1.0 = très intense)
    """
    style = MysticalStyle(
        mystical_intensity=intensity,
        wisdom_tone=True,
        use_metaphors=True,
        hermetic_vocabulary=True
    )
    
    return MysticalResponseProcessor(style)


# Fonction d'intégration pour LangChain
def enhance_langchain_with_mystical_persona(pipeline, intensity: float = 0.7):
    """
    Améliore un pipeline LangChain avec la persona mystique.
    """
    processor = create_mystical_processor(intensity)
    
    # Monkey patch de la méthode query
    original_query = pipeline.query
    
    async def mystical_query(question: str, session_id: str = "default") -> Dict[str, Any]:
        # Appel original
        original_result = await original_query(question, session_id)
        
        # Transformation mystique
        mystical_result = processor.process_langchain_response(
            query=question,
            response=original_result["answer"], 
            sources=original_result.get("sources", [])
        )
        
        # Fusion des résultats
        enhanced_result = {
            **original_result,
            "answer": mystical_result["mystical_answer"],
            "sources": mystical_result["sacred_sources"],
            "mystical_metadata": mystical_result["spiritual_metadata"]
        }
        
        return enhanced_result
    
    pipeline.query = mystical_query
    return pipeline


if __name__ == "__main__":
    # Test du module
    processor = create_mystical_processor(intensity=0.8)
    
    test_response = "John Dee était un érudit anglais qui étudiait l'alchimie et communiquait avec les anges."
    test_sources = [{"content": "Texte sur John Dee...", "metadata": {"source": "john-dee-book.pdf"}}]
    
    result = processor.process_langchain_response(
        query="Parle-moi de John Dee",
        response=test_response,
        sources=test_sources
    )
    
    print("🔮 RÉPONSE MYSTIQUE :")
    print(result["mystical_answer"])
    print("\n" + "="*50)
    print("📚 SOURCES SACRÉES :")
    for source in result["sacred_sources"]:
        print(f"- {source['ancient_source']}: {source['spiritual_resonance']}") 