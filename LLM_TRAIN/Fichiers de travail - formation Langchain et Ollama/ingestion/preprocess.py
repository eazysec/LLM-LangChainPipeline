"""
Module de prétraitement des documents.
Nettoie et normalise le texte avant l'indexation.
"""

import re
import logging
from typing import List, Dict, Any, Optional
import unicodedata
import os

logger = logging.getLogger(__name__)


class DocumentPreprocessor:
    """Préprocesseur pour nettoyer et normaliser les documents."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le préprocesseur.
        
        Args:
            config: Configuration du préprocesseur
        """
        self.config = config or {}
        
        # Expressions régulières pour le nettoyage
        self.patterns = {
            'multiple_spaces': re.compile(r'\s+'),
            'multiple_newlines': re.compile(r'\n\s*\n'),
            'urls': re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            'emails': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone_numbers': re.compile(r'(\+\d{1,3}\s?)?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,9}'),
            'special_chars': re.compile(r'[^\w\s\-.,;:!?()[\]{}\"\'`~@#$%^&*+=|\\/<>]'),
            'page_numbers': re.compile(r'--- Page \d+ ---'),
            'headers_footers': re.compile(r'^(page|chapter|section)\s+\d+', re.IGNORECASE | re.MULTILINE),
        }
    
    def preprocess_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prétraite un document complet.
        
        Args:
            document: Document à prétraiter
            
        Returns:
            Document prétraité
        """
        try:
            content = document.get('content', '')
            metadata = document.get('metadata', {})
            
            # Nettoyer le contenu
            cleaned_content = self.clean_text(content)
            
            # Normaliser le texte
            normalized_content = self.normalize_text(cleaned_content)
            
            # Extraire des métadonnées additionnelles
            extracted_metadata = self.extract_metadata(normalized_content)
            metadata.update(extracted_metadata)
            
            return {
                'content': normalized_content,
                'metadata': metadata,
                'original_length': len(content),
                'processed_length': len(normalized_content)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du prétraitement: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """
        Nettoie le texte en supprimant les éléments indésirables.
        
        Args:
            text: Texte à nettoyer
            
        Returns:
            Texte nettoyé
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Supprimer les caractères de contrôle
        text = ''.join(char for char in text if unicodedata.category(char) not in ['Cc', 'Cf'])
        
        # Nettoyer selon la configuration
        if self.config.get('remove_urls', True):
            text = self.patterns['urls'].sub('', text)
        
        if self.config.get('remove_emails', True):
            text = self.patterns['emails'].sub('', text)
        
        if self.config.get('remove_phone_numbers', True):
            text = self.patterns['phone_numbers'].sub('', text)
        
        if self.config.get('remove_page_numbers', True):
            text = self.patterns['page_numbers'].sub('', text)
        
        if self.config.get('remove_headers_footers', True):
            text = self.patterns['headers_footers'].sub('', text)
        
        # Normaliser les espaces et nouvelles lignes
        text = self.patterns['multiple_spaces'].sub(' ', text)
        text = self.patterns['multiple_newlines'].sub('\n\n', text)
        
        return text.strip()
    
    def normalize_text(self, text: str) -> str:
        """
        Normalise le texte.
        
        Args:
            text: Texte à normaliser
            
        Returns:
            Texte normalisé
        """
        if not text:
            return ""
        
        # Normalisation Unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Convertir en minuscules si configuré
        if self.config.get('lowercase', False):
            text = text.lower()
        
        # Supprimer les caractères spéciaux si configuré
        if self.config.get('remove_special_chars', False):
            text = self.patterns['special_chars'].sub(' ', text)
            text = self.patterns['multiple_spaces'].sub(' ', text)
        
        return text.strip()
    
    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extrait des métadonnées du texte.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Métadonnées extraites
        """
        metadata = {}
        
        if not text:
            return metadata
        
        # Statistiques de base
        metadata['word_count'] = len(text.split())
        metadata['char_count'] = len(text)
        metadata['line_count'] = len(text.split('\n'))
        metadata['paragraph_count'] = len([p for p in text.split('\n\n') if p.strip()])
        
        # Détecter la langue (simple heuristique)
        metadata['language'] = self._detect_language(text)
        
        # Extraire les titres potentiels
        metadata['potential_titles'] = self._extract_titles(text)
        
        # Détecter le type de contenu
        metadata['content_type'] = self._detect_content_type(text)
        
        return metadata
    
    def _detect_language(self, text: str) -> str:
        """Détecte la langue du texte (heuristique simple)."""
        # Mots français communs
        french_words = ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour']
        
        # Mots anglais communs
        english_words = ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for']
        
        words = text.lower().split()[:100]  # Analyser les 100 premiers mots
        
        french_count = sum(1 for word in words if word in french_words)
        english_count = sum(1 for word in words if word in english_words)
        
        if french_count > english_count:
            return 'fr'
        elif english_count > french_count:
            return 'en'
        else:
            return 'unknown'
    
    def _extract_titles(self, text: str) -> List[str]:
        """Extrait les titres potentiels du texte."""
        lines = text.split('\n')
        titles = []
        
        for line in lines:
            line = line.strip()
            # Heuristiques pour détecter les titres
            if (len(line) < 100 and 
                len(line) > 5 and 
                not line.endswith('.') and 
                (line.isupper() or line.istitle())):
                titles.append(line)
        
        return titles[:5]  # Limiter à 5 titres
    
    def _detect_content_type(self, text: str) -> str:
        """Détecte le type de contenu."""
        text_lower = text.lower()
        
        # Heuristiques simples
        if any(keyword in text_lower for keyword in ['article', 'résumé', 'abstract']):
            return 'article'
        elif any(keyword in text_lower for keyword in ['chapitre', 'chapter', 'section']):
            return 'book'
        elif any(keyword in text_lower for keyword in ['email', 'courrier', 'message']):
            return 'email'
        elif any(keyword in text_lower for keyword in ['rapport', 'report', 'analyse']):
            return 'report'
        else:
            return 'document'
    
    def preprocess_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prétraite un lot de documents.
        
        Args:
            documents: Liste de documents à prétraiter
            
        Returns:
            Liste de documents prétraités
        """
        processed_documents = []
        
        for i, doc in enumerate(documents):
            try:
                processed_doc = self.preprocess_document(doc)
                processed_documents.append(processed_doc)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Prétraitement: {i + 1}/{len(documents)} documents")
                    
            except Exception as e:
                logger.error(f"Erreur lors du prétraitement du document {i}: {e}")
                # Continuer avec le document original
                processed_documents.append(doc)
        
        logger.info(f"Prétraitement terminé: {len(processed_documents)} documents")
        return processed_documents


# Fonctions utilitaires
def clean_filename(filename: str) -> str:
    """Nettoie un nom de fichier."""
    # Supprimer les caractères non autorisés
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limiter la longueur
    if len(cleaned) > 255:
        name, ext = os.path.splitext(cleaned)
        cleaned = name[:255-len(ext)] + ext
    return cleaned


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extrait des mots-clés simples du texte.
    
    Args:
        text: Texte à analyser
        max_keywords: Nombre maximum de mots-clés
        
    Returns:
        Liste de mots-clés
    """
    if not text:
        return []
    
    # Mots vides français et anglais
    stop_words = {
        'le', 'de', 'et', 'à', 'un', 'il', 'être', 'avoir', 'que', 'pour', 'dans', 'ce', 'son',
        'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus', 'par', 'grand', 'en', 'la',
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not',
        'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from'
    }
    
    # Extraire les mots
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', text.lower())
    
    # Filtrer les mots vides et compter les occurrences
    word_counts = {}
    for word in words:
        if word not in stop_words:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Trier par fréquence et retourner les top mots-clés
    keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in keywords[:max_keywords]] 