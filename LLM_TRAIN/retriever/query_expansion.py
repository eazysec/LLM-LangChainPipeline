"""
Module d'expansion de requête pour améliorer la recherche.
"""

import logging
from typing import List, Dict, Any, Optional
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueryVariation:
    """Variation d'une requête."""
    text: str
    score: float
    method: str


class QueryExpander:
    """Expandeur de requête pour améliorer la recherche sémantique."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise l'expandeur de requête.
        
        Args:
            config: Configuration de l'expansion
        """
        self.config = config or {}
        
        # Configuration
        self.max_variations = self.config.get('max_variations', 3)
        self.enable_synonyms = self.config.get('enable_synonyms', True)
        self.enable_reformulation = self.config.get('enable_reformulation', True)
        self.enable_decomposition = self.config.get('enable_decomposition', True)
        
        # Dictionnaire de synonymes simple (peut être étendu)
        self.synonyms_dict = {
            'comment': ['comment', 'pourquoi', 'de quelle manière'],
            'quoi': ['quoi', 'que', 'qu\'est-ce que'],
            'où': ['où', 'dans quel endroit', 'à quel endroit'],
            'quand': ['quand', 'à quel moment', 'depuis quand'],
            'qui': ['qui', 'quelle personne', 'quel individu'],
            'problème': ['problème', 'souci', 'difficulté', 'erreur'],
            'solution': ['solution', 'résolution', 'réponse', 'remède'],
            'méthode': ['méthode', 'procédure', 'approche', 'technique'],
            'installer': ['installer', 'configurer', 'mettre en place', 'déployer'],
            'erreur': ['erreur', 'bug', 'problème', 'dysfonctionnement']
        }
        
        logger.info("Expandeur de requête initialisé")
    
    def expand(self, query: str) -> List[str]:
        """
        Expanse une requête en générant des variations.
        
        Args:
            query: Requête originale
            
        Returns:
            Liste des variations de requête
        """
        try:
            variations = [QueryVariation(query, 1.0, 'original')]
            
            # Générer différents types de variations
            if self.enable_synonyms:
                variations.extend(self._generate_synonym_variations(query))
            
            if self.enable_reformulation:
                variations.extend(self._generate_reformulations(query))
            
            if self.enable_decomposition:
                variations.extend(self._generate_decompositions(query))
            
            # Trier par score et limiter le nombre
            variations.sort(key=lambda x: x.score, reverse=True)
            variations = variations[:self.max_variations]
            
            # Extraire les textes
            expanded_queries = [v.text for v in variations]
            
            logger.debug(f"Requête expansée: {len(expanded_queries)} variations")
            return expanded_queries
            
        except Exception as e:
            logger.error(f"Erreur lors de l'expansion de requête: {e}")
            return [query]  # Retourner la requête originale en cas d'erreur
    
    def _generate_synonym_variations(self, query: str) -> List[QueryVariation]:
        """Génère des variations basées sur les synonymes."""
        variations = []
        
        try:
            words = query.lower().split()
            
            for word in words:
                if word in self.synonyms_dict:
                    synonyms = self.synonyms_dict[word]
                    
                    for synonym in synonyms[1:]:  # Exclure le mot original
                        new_query = query.replace(word, synonym, 1)
                        if new_query != query:
                            variations.append(QueryVariation(
                                text=new_query,
                                score=0.8,
                                method='synonym'
                            ))
                            
        except Exception as e:
            logger.warning(f"Erreur lors de la génération de synonymes: {e}")
        
        return variations
    
    def _generate_reformulations(self, query: str) -> List[QueryVariation]:
        """Génère des reformulations de la requête."""
        variations = []
        
        try:
            # Reformulations basées sur des patterns
            reformulation_patterns = [
                (r'^comment (.+)', r'de quelle manière \1'),
                (r'^pourquoi (.+)', r'quelle est la raison pour laquelle \1'),
                (r'^qu\'est-ce que (.+)', r'définition de \1'),
                (r'^où (.+)', r'emplacement de \1'),
                (r'^quand (.+)', r'moment où \1'),
                (r'(.+) ne fonctionne pas', r'problème avec \1'),
                (r'erreur (.+)', r'dysfonctionnement \1'),
            ]
            
            query_lower = query.lower()
            
            for pattern, replacement in reformulation_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    reformulated = re.sub(pattern, replacement, query_lower)
                    if reformulated != query_lower:
                        variations.append(QueryVariation(
                            text=reformulated,
                            score=0.7,
                            method='reformulation'
                        ))
                        
        except Exception as e:
            logger.warning(f"Erreur lors de la reformulation: {e}")
        
        return variations
    
    def _generate_decompositions(self, query: str) -> List[QueryVariation]:
        """Décompose la requête en sous-parties."""
        variations = []
        
        try:
            # Décomposer les questions complexes
            if ' et ' in query.lower():
                parts = query.lower().split(' et ')
                for part in parts:
                    part = part.strip()
                    if len(part) > 5:  # Ignorer les parties trop courtes
                        variations.append(QueryVariation(
                            text=part,
                            score=0.6,
                            method='decomposition'
                        ))
            
            # Extraire les concepts clés
            key_concepts = self._extract_key_concepts(query)
            for concept in key_concepts:
                if concept.lower() != query.lower():
                    variations.append(QueryVariation(
                        text=concept,
                        score=0.5,
                        method='key_concept'
                    ))
                    
        except Exception as e:
            logger.warning(f"Erreur lors de la décomposition: {e}")
        
        return variations
    
    def _extract_key_concepts(self, query: str) -> List[str]:
        """Extrait les concepts clés d'une requête."""
        concepts = []
        
        try:
            # Mots vides à ignorer
            stop_words = {
                'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'mais',
                'pour', 'avec', 'sans', 'dans', 'sur', 'sous', 'par', 'où', 'comment',
                'que', 'qui', 'quoi', 'quand', 'pourquoi', 'est', 'sont', 'avoir', 'être'
            }
            
            # Extraire les mots significatifs
            words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', query.lower())
            significant_words = [w for w in words if w not in stop_words]
            
            # Créer des concepts à partir des mots significatifs
            if len(significant_words) >= 2:
                # Prendre les 2-3 mots les plus importants
                concepts.extend(significant_words[:3])
                
                # Créer des combinaisons
                if len(significant_words) >= 2:
                    concepts.append(' '.join(significant_words[:2]))
                    
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction de concepts: {e}")
        
        return concepts
    
    def add_synonyms(self, word: str, synonyms: List[str]):
        """
        Ajoute des synonymes au dictionnaire.
        
        Args:
            word: Mot principal
            synonyms: Liste de synonymes
        """
        if word not in self.synonyms_dict:
            self.synonyms_dict[word] = [word]
        
        for synonym in synonyms:
            if synonym not in self.synonyms_dict[word]:
                self.synonyms_dict[word].append(synonym)
        
        logger.info(f"Synonymes ajoutés pour '{word}': {synonyms}")
    
    def get_synonyms(self, word: str) -> List[str]:
        """
        Récupère les synonymes d'un mot.
        
        Args:
            word: Mot à rechercher
            
        Returns:
            Liste des synonymes
        """
        return self.synonyms_dict.get(word.lower(), [word])
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyse une requête pour identifier ses caractéristiques.
        
        Args:
            query: Requête à analyser
            
        Returns:
            Dictionnaire d'analyse
        """
        analysis = {
            'length': len(query),
            'word_count': len(query.split()),
            'has_question_words': False,
            'question_type': 'unknown',
            'key_concepts': [],
            'complexity': 'simple'
        }
        
        try:
            query_lower = query.lower()
            
            # Détecter les mots interrogatifs
            question_words = ['comment', 'pourquoi', 'quoi', 'que', 'où', 'quand', 'qui']
            for word in question_words:
                if word in query_lower:
                    analysis['has_question_words'] = True
                    analysis['question_type'] = word
                    break
            
            # Extraire les concepts clés
            analysis['key_concepts'] = self._extract_key_concepts(query)
            
            # Évaluer la complexité
            if analysis['word_count'] > 10 or ' et ' in query_lower or ' ou ' in query_lower:
                analysis['complexity'] = 'complex'
            elif analysis['word_count'] > 5:
                analysis['complexity'] = 'medium'
            
            logger.debug(f"Analyse de requête: {analysis}")
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'analyse de requête: {e}")
        
        return analysis


# Fonctions utilitaires
def expand_query_simple(query: str, synonyms_dict: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """
    Fonction simple d'expansion de requête.
    
    Args:
        query: Requête à expander
        synonyms_dict: Dictionnaire de synonymes optionnel
        
    Returns:
        Liste des variations de requête
    """
    expander = QueryExpander()
    
    if synonyms_dict:
        expander.synonyms_dict.update(synonyms_dict)
    
    return expander.expand(query)


def create_domain_specific_expander(domain: str) -> QueryExpander:
    """
    Crée un expandeur spécialisé pour un domaine.
    
    Args:
        domain: Domaine de spécialisation ('tech', 'medical', 'legal', etc.)
        
    Returns:
        Expandeur configuré pour le domaine
    """
    config = {'max_variations': 5}
    expander = QueryExpander(config)
    
    # Ajouter des synonymes spécifiques au domaine
    if domain == 'tech':
        tech_synonyms = {
            'bug': ['bug', 'erreur', 'problème', 'dysfonctionnement'],
            'installer': ['installer', 'configurer', 'setup', 'déployer'],
            'API': ['API', 'interface', 'service web', 'endpoint'],
            'base de données': ['base de données', 'BDD', 'database', 'DB']
        }
        for word, synonyms in tech_synonyms.items():
            expander.add_synonyms(word, synonyms)
    
    elif domain == 'medical':
        medical_synonyms = {
            'symptôme': ['symptôme', 'signe', 'manifestation'],
            'traitement': ['traitement', 'thérapie', 'soin', 'remède'],
            'diagnostic': ['diagnostic', 'évaluation', 'examen']
        }
        for word, synonyms in medical_synonyms.items():
            expander.add_synonyms(word, synonyms)
    
    return expander 