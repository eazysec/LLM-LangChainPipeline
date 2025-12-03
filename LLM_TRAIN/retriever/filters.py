"""
Module de filtres pour les métadonnées des documents.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import re

logger = logging.getLogger(__name__)


class MetadataFilter(ABC):
    """Classe abstraite pour les filtres de métadonnées."""
    
    @abstractmethod
    def apply(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Applique le filtre aux résultats.
        
        Args:
            results: Liste des résultats à filtrer
            
        Returns:
            Liste des résultats filtrés
        """
        pass
    
    @abstractmethod
    def describe(self) -> str:
        """Retourne une description du filtre."""
        pass


class SourceFilter(MetadataFilter):
    """Filtre par source de document."""
    
    def __init__(self, allowed_sources: List[str], exclude: bool = False):
        """
        Initialise le filtre de source.
        
        Args:
            allowed_sources: Liste des sources autorisées
            exclude: Si True, exclut les sources listées
        """
        self.allowed_sources = [s.lower() for s in allowed_sources]
        self.exclude = exclude
    
    def apply(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Applique le filtre de source."""
        filtered = []
        
        for result in results:
            metadata = result.get('metadata', {})
            source = metadata.get('source', '').lower()
            
            # Vérifier si la source correspond
            matches = any(allowed in source for allowed in self.allowed_sources)
            
            # Inclure ou exclure selon la configuration
            if (matches and not self.exclude) or (not matches and self.exclude):
                filtered.append(result)
        
        logger.debug(f"Filtre source: {len(results)} -> {len(filtered)} résultats")
        return filtered
    
    def describe(self) -> str:
        """Décrit le filtre."""
        action = "exclut" if self.exclude else "inclut"
        return f"Filtre source ({action}): {', '.join(self.allowed_sources)}"


class DateFilter(MetadataFilter):
    """Filtre par date de modification/création."""
    
    def __init__(self, 
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None,
                 days_ago: Optional[int] = None,
                 date_field: str = 'modified_at'):
        """
        Initialise le filtre de date.
        
        Args:
            start_date: Date de début (incluse)
            end_date: Date de fin (incluse)
            days_ago: Nombre de jours dans le passé (alternatif à start_date)
            date_field: Champ de métadonnée contenant la date
        """
        self.start_date = start_date
        self.end_date = end_date
        self.date_field = date_field
        
        # Calculer la date de début à partir de days_ago
        if days_ago is not None and start_date is None:
            self.start_date = datetime.now() - timedelta(days=days_ago)
    
    def apply(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Applique le filtre de date."""
        filtered = []
        
        for result in results:
            metadata = result.get('metadata', {})
            date_value = metadata.get(self.date_field)
            
            if date_value is None:
                continue
            
            try:
                # Convertir en datetime si nécessaire
                if isinstance(date_value, (int, float)):
                    doc_date = datetime.fromtimestamp(date_value)
                elif isinstance(date_value, str):
                    doc_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                elif isinstance(date_value, datetime):
                    doc_date = date_value
                else:
                    continue
                
                # Vérifier les critères de date
                include = True
                
                if self.start_date and doc_date < self.start_date:
                    include = False
                
                if self.end_date and doc_date > self.end_date:
                    include = False
                
                if include:
                    filtered.append(result)
                    
            except (ValueError, TypeError) as e:
                logger.debug(f"Erreur de conversion de date: {e}")
                continue
        
        logger.debug(f"Filtre date: {len(results)} -> {len(filtered)} résultats")
        return filtered
    
    def describe(self) -> str:
        """Décrit le filtre."""
        parts = []
        if self.start_date:
            parts.append(f"après {self.start_date.strftime('%Y-%m-%d')}")
        if self.end_date:
            parts.append(f"avant {self.end_date.strftime('%Y-%m-%d')}")
        
        criteria = " et ".join(parts) if parts else "toutes dates"
        return f"Filtre date ({self.date_field}): {criteria}"


class ExtensionFilter(MetadataFilter):
    """Filtre par extension de fichier."""
    
    def __init__(self, allowed_extensions: List[str], exclude: bool = False):
        """
        Initialise le filtre d'extension.
        
        Args:
            allowed_extensions: Liste des extensions autorisées (avec ou sans point)
            exclude: Si True, exclut les extensions listées
        """
        # Normaliser les extensions
        self.allowed_extensions = []
        for ext in allowed_extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            self.allowed_extensions.append(ext.lower())
        
        self.exclude = exclude
    
    def apply(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Applique le filtre d'extension."""
        filtered = []
        
        for result in results:
            metadata = result.get('metadata', {})
            extension = metadata.get('extension', '').lower()
            
            # Vérifier si l'extension correspond
            matches = extension in self.allowed_extensions
            
            # Inclure ou exclure selon la configuration
            if (matches and not self.exclude) or (not matches and self.exclude):
                filtered.append(result)
        
        logger.debug(f"Filtre extension: {len(results)} -> {len(filtered)} résultats")
        return filtered
    
    def describe(self) -> str:
        """Décrit le filtre."""
        action = "exclut" if self.exclude else "inclut"
        return f"Filtre extension ({action}): {', '.join(self.allowed_extensions)}"


class SizeFilter(MetadataFilter):
    """Filtre par taille de fichier."""
    
    def __init__(self, 
                 min_size: Optional[int] = None,
                 max_size: Optional[int] = None,
                 size_field: str = 'size'):
        """
        Initialise le filtre de taille.
        
        Args:
            min_size: Taille minimale en bytes
            max_size: Taille maximale en bytes
            size_field: Champ de métadonnée contenant la taille
        """
        self.min_size = min_size
        self.max_size = max_size
        self.size_field = size_field
    
    def apply(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Applique le filtre de taille."""
        filtered = []
        
        for result in results:
            metadata = result.get('metadata', {})
            size = metadata.get(self.size_field)
            
            if size is None:
                continue
            
            try:
                size = int(size)
                
                # Vérifier les critères de taille
                include = True
                
                if self.min_size is not None and size < self.min_size:
                    include = False
                
                if self.max_size is not None and size > self.max_size:
                    include = False
                
                if include:
                    filtered.append(result)
                    
            except (ValueError, TypeError):
                continue
        
        logger.debug(f"Filtre taille: {len(results)} -> {len(filtered)} résultats")
        return filtered
    
    def describe(self) -> str:
        """Décrit le filtre."""
        parts = []
        if self.min_size:
            parts.append(f"min {self.min_size} bytes")
        if self.max_size:
            parts.append(f"max {self.max_size} bytes")
        
        criteria = " et ".join(parts) if parts else "toutes tailles"
        return f"Filtre taille: {criteria}"


class KeywordFilter(MetadataFilter):
    """Filtre par mots-clés dans les métadonnées."""
    
    def __init__(self, 
                 keywords: List[str],
                 field: str = 'content',
                 case_sensitive: bool = False,
                 match_all: bool = False):
        """
        Initialise le filtre de mots-clés.
        
        Args:
            keywords: Liste des mots-clés à rechercher
            field: Champ où rechercher ('content', 'filename', etc.)
            case_sensitive: Sensible à la casse
            match_all: Si True, tous les mots-clés doivent être présents
        """
        self.keywords = keywords if case_sensitive else [k.lower() for k in keywords]
        self.field = field
        self.case_sensitive = case_sensitive
        self.match_all = match_all
    
    def apply(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Applique le filtre de mots-clés."""
        filtered = []
        
        for result in results:
            # Déterminer le texte à analyser
            if self.field == 'content':
                text = result.get('content', '')
            else:
                metadata = result.get('metadata', {})
                text = str(metadata.get(self.field, ''))
            
            if not self.case_sensitive:
                text = text.lower()
            
            # Vérifier la présence des mots-clés
            if self.match_all:
                # Tous les mots-clés doivent être présents
                if all(keyword in text for keyword in self.keywords):
                    filtered.append(result)
            else:
                # Au moins un mot-clé doit être présent
                if any(keyword in text for keyword in self.keywords):
                    filtered.append(result)
        
        logger.debug(f"Filtre mots-clés: {len(results)} -> {len(filtered)} résultats")
        return filtered
    
    def describe(self) -> str:
        """Décrit le filtre."""
        logic = "TOUS" if self.match_all else "AU MOINS UN"
        return f"Filtre mots-clés ({self.field}, {logic}): {', '.join(self.keywords)}"


class RegexFilter(MetadataFilter):
    """Filtre par expression régulière."""
    
    def __init__(self, 
                 pattern: str,
                 field: str = 'content',
                 flags: int = re.IGNORECASE):
        """
        Initialise le filtre regex.
        
        Args:
            pattern: Expression régulière
            field: Champ où appliquer le pattern
            flags: Flags regex (par défaut: ignore case)
        """
        self.pattern = re.compile(pattern, flags)
        self.field = field
        self.pattern_str = pattern
    
    def apply(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Applique le filtre regex."""
        filtered = []
        
        for result in results:
            # Déterminer le texte à analyser
            if self.field == 'content':
                text = result.get('content', '')
            else:
                metadata = result.get('metadata', {})
                text = str(metadata.get(self.field, ''))
            
            # Vérifier si le pattern correspond
            if self.pattern.search(text):
                filtered.append(result)
        
        logger.debug(f"Filtre regex: {len(results)} -> {len(filtered)} résultats")
        return filtered
    
    def describe(self) -> str:
        """Décrit le filtre."""
        return f"Filtre regex ({self.field}): {self.pattern_str}"


class SimilarityFilter(MetadataFilter):
    """Filtre par seuil de similarité."""
    
    def __init__(self, min_similarity: float, max_similarity: float = 1.0):
        """
        Initialise le filtre de similarité.
        
        Args:
            min_similarity: Similarité minimale
            max_similarity: Similarité maximale
        """
        self.min_similarity = min_similarity
        self.max_similarity = max_similarity
    
    def apply(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Applique le filtre de similarité."""
        filtered = []
        
        for result in results:
            similarity = result.get('similarity', 0.0)
            
            if self.min_similarity <= similarity <= self.max_similarity:
                filtered.append(result)
        
        logger.debug(f"Filtre similarité: {len(results)} -> {len(filtered)} résultats")
        return filtered
    
    def describe(self) -> str:
        """Décrit le filtre."""
        return f"Filtre similarité: {self.min_similarity:.2f} - {self.max_similarity:.2f}"


# Fonctions utilitaires
def create_composite_filter(filters: List[MetadataFilter]) -> 'CompositeFilter':
    """
    Crée un filtre composite qui applique plusieurs filtres.
    
    Args:
        filters: Liste des filtres à combiner
        
    Returns:
        Filtre composite
    """
    return CompositeFilter(filters)


class CompositeFilter(MetadataFilter):
    """Filtre composite qui combine plusieurs filtres."""
    
    def __init__(self, filters: List[MetadataFilter]):
        """
        Initialise le filtre composite.
        
        Args:
            filters: Liste des filtres à appliquer
        """
        self.filters = filters
    
    def apply(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Applique tous les filtres en séquence."""
        filtered = results
        
        for filter_obj in self.filters:
            filtered = filter_obj.apply(filtered)
        
        logger.debug(f"Filtre composite: {len(results)} -> {len(filtered)} résultats")
        return filtered
    
    def describe(self) -> str:
        """Décrit le filtre composite."""
        descriptions = [f.describe() for f in self.filters]
        return f"Filtre composite: {' ET '.join(descriptions)}"


def create_recent_documents_filter(days: int = 30) -> DateFilter:
    """
    Crée un filtre pour les documents récents.
    
    Args:
        days: Nombre de jours dans le passé
        
    Returns:
        Filtre de date
    """
    return DateFilter(days_ago=days)


def create_pdf_only_filter() -> ExtensionFilter:
    """Crée un filtre pour les fichiers PDF uniquement."""
    return ExtensionFilter(['.pdf'])


def create_large_files_filter(min_size_mb: int = 1) -> SizeFilter:
    """
    Crée un filtre pour les gros fichiers.
    
    Args:
        min_size_mb: Taille minimale en MB
        
    Returns:
        Filtre de taille
    """
    min_size_bytes = min_size_mb * 1024 * 1024
    return SizeFilter(min_size=min_size_bytes) 