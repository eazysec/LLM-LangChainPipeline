"""
Module de découpage des documents en chunks pour l'indexation vectorielle.
"""

import logging
from typing import List, Dict, Any, Optional
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Représente un chunk de texte."""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    start_index: int
    end_index: int


class DocumentChunker:
    """Découpe les documents en chunks optimaux pour l'indexation."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, min_chunk_size: int = 50):
        """
        Initialise le chunker.
        
        Args:
            chunk_size: Taille maximale d'un chunk en caractères
            chunk_overlap: Chevauchement entre chunks en caractères
            min_chunk_size: Taille minimale d'un chunk
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Patterns pour détecter les séparateurs naturels
        self.separators = [
            '\n\n\n',  # Triple saut de ligne
            '\n\n',    # Double saut de ligne
            '\n',      # Saut de ligne simple
            '. ',      # Fin de phrase
            '! ',      # Exclamation
            '? ',      # Question
            '; ',      # Point-virgule
            ', ',      # Virgule
            ' ',       # Espace
        ]
    
    def chunk_document(self, document: Dict[str, Any]) -> List[Chunk]:
        """
        Découpe un document en chunks.
        
        Args:
            document: Document à découper
            
        Returns:
            Liste de chunks
        """
        content = document.get('content', '')
        metadata = document.get('metadata', {})
        
        if not content or len(content) < self.min_chunk_size:
            logger.warning(f"Document trop court pour être découpé: {len(content)} caractères")
            return []
        
        # Choisir la stratégie de découpage
        if self._has_clear_structure(content):
            chunks = self._chunk_by_structure(content, metadata)
        else:
            chunks = self._chunk_by_size(content, metadata)
        
        # Filtrer les chunks trop petits
        valid_chunks = [chunk for chunk in chunks if len(chunk.content) >= self.min_chunk_size]
        
        logger.info(f"Document découpé en {len(valid_chunks)} chunks")
        return valid_chunks
    
    def _has_clear_structure(self, content: str) -> bool:
        """Détermine si le document a une structure claire."""
        # Compter les marqueurs de structure
        structure_markers = [
            r'^#{1,6}\s+',          # Titres Markdown
            r'^\d+\.\s+',           # Listes numérotées
            r'^[A-Z][A-Z\s]{5,}$',  # Titres en majuscules
            r'--- Page \d+ ---',    # Marqueurs de page
        ]
        
        lines = content.split('\n')
        structure_count = 0
        
        for line in lines:
            for pattern in structure_markers:
                if re.match(pattern, line.strip(), re.MULTILINE):
                    structure_count += 1
                    break
        
        # Si plus de 5% des lignes ont des marqueurs de structure
        return structure_count > len(lines) * 0.05
    
    def _chunk_by_structure(self, content: str, base_metadata: Dict[str, Any]) -> List[Chunk]:
        """Découpe le document en utilisant sa structure."""
        chunks = []
        sections = self._split_by_structure(content)
        
        for i, section in enumerate(sections):
            if len(section['content']) <= self.chunk_size:
                # Section assez petite pour être un chunk
                chunk = self._create_chunk(
                    content=section['content'],
                    base_metadata=base_metadata,
                    chunk_index=i,
                    section_title=section.get('title', ''),
                    start_index=section['start_index'],
                    end_index=section['end_index']
                )
                chunks.append(chunk)
            else:
                # Section trop grande, la découper par taille
                section_chunks = self._chunk_by_size(
                    section['content'], 
                    base_metadata, 
                    section_title=section.get('title', ''),
                    base_index=i * 1000
                )
                chunks.extend(section_chunks)
        
        return chunks
    
    def _chunk_by_size(self, content: str, base_metadata: Dict[str, Any], 
                      section_title: str = '', base_index: int = 0) -> List[Chunk]:
        """Découpe le document par taille avec chevauchement."""
        chunks = []
        start = 0
        chunk_index = base_index
        
        while start < len(content):
            # Déterminer la fin du chunk
            end = start + self.chunk_size
            
            if end >= len(content):
                # Dernier chunk
                chunk_content = content[start:]
            else:
                # Chercher un point de coupe naturel
                cut_point = self._find_natural_cut(content, start, end)
                chunk_content = content[start:cut_point]
            
            # Créer le chunk si suffisamment long
            if len(chunk_content.strip()) >= self.min_chunk_size:
                chunk = self._create_chunk(
                    content=chunk_content.strip(),
                    base_metadata=base_metadata,
                    chunk_index=chunk_index,
                    section_title=section_title,
                    start_index=start,
                    end_index=start + len(chunk_content)
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Calculer le prochain point de départ avec chevauchement
            start = start + self.chunk_size - self.chunk_overlap
            
            # Éviter les boucles infinies
            if start <= chunks[-1].start_index if chunks else 0:
                start += self.min_chunk_size
        
        return chunks
    
    def _split_by_structure(self, content: str) -> List[Dict[str, Any]]:
        """Divise le contenu en sections basées sur la structure."""
        sections = []
        lines = content.split('\n')
        current_section = {'title': '', 'content': '', 'start_index': 0}
        start_index = 0
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Détecter un nouveau titre/section
            if self._is_section_header(line_stripped):
                # Sauvegarder la section précédente
                if current_section['content'].strip():
                    current_section['end_index'] = start_index + len('\n'.join(lines[:i]))
                    sections.append(current_section.copy())
                
                # Commencer une nouvelle section
                current_section = {
                    'title': line_stripped,
                    'content': '',
                    'start_index': start_index + len('\n'.join(lines[:i]))
                }
            else:
                # Ajouter la ligne à la section courante
                if current_section['content']:
                    current_section['content'] += '\n'
                current_section['content'] += line
        
        # Ajouter la dernière section
        if current_section['content'].strip():
            current_section['end_index'] = len(content)
            sections.append(current_section)
        
        return sections
    
    def _is_section_header(self, line: str) -> bool:
        """Détermine si une ligne est un en-tête de section."""
        if not line:
            return False
        
        # Patterns pour détecter les en-têtes
        header_patterns = [
            r'^#{1,6}\s+',          # Markdown headers
            r'^\d+\.\s+[A-Z]',      # Numérotation "1. Titre"
            r'^[A-Z][A-Z\s]{5,}$',  # Titre en majuscules
            r'^Chapter \d+',        # "Chapter X"
            r'^Section \d+',        # "Section X"
        ]
        
        for pattern in header_patterns:
            if re.match(pattern, line):
                return True
        
        # Heuristique: ligne courte, pas de ponctuation finale
        if (len(line) < 100 and 
            not line.endswith('.') and 
            not line.endswith(',') and
            len(line.split()) > 1):
            return True
        
        return False
    
    def _find_natural_cut(self, content: str, start: int, end: int) -> int:
        """Trouve un point de coupe naturel près de la position end."""
        # Zone de recherche pour le point de coupe (10% de la taille du chunk)
        search_range = min(self.chunk_size // 10, 50)
        search_start = max(start, end - search_range)
        search_end = min(len(content), end + search_range)
        
        # Chercher le meilleur séparateur
        for separator in self.separators:
            # Chercher depuis la fin vers le début
            for pos in range(search_end - len(separator), search_start - 1, -1):
                if content[pos:pos + len(separator)] == separator:
                    return pos + len(separator)
        
        # Aucun séparateur trouvé, couper à la position originale
        return end
    
    def _create_chunk(self, content: str, base_metadata: Dict[str, Any], 
                     chunk_index: int, section_title: str = '', 
                     start_index: int = 0, end_index: int = 0) -> Chunk:
        """Crée un objet Chunk."""
        # Créer les métadonnées du chunk
        chunk_metadata = base_metadata.copy()
        chunk_metadata.update({
            'chunk_index': chunk_index,
            'chunk_size': len(content),
            'section_title': section_title,
            'word_count': len(content.split()),
        })
        
        # Générer un ID unique pour le chunk
        source = base_metadata.get('source', 'unknown')
        chunk_id = f"{source}#{chunk_index}"
        
        return Chunk(
            content=content,
            metadata=chunk_metadata,
            chunk_id=chunk_id,
            start_index=start_index,
            end_index=end_index
        )
    
    def chunk_batch(self, documents: List[Dict[str, Any]]) -> List[List[Chunk]]:
        """
        Découpe un lot de documents.
        
        Args:
            documents: Liste de documents à découper
            
        Returns:
            Liste de listes de chunks (une liste par document)
        """
        all_chunks = []
        
        for i, doc in enumerate(documents):
            try:
                doc_chunks = self.chunk_document(doc)
                all_chunks.append(doc_chunks)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Découpage: {i + 1}/{len(documents)} documents")
                    
            except Exception as e:
                logger.error(f"Erreur lors du découpage du document {i}: {e}")
                all_chunks.append([])  # Liste vide en cas d'erreur
        
        total_chunks = sum(len(chunks) for chunks in all_chunks)
        logger.info(f"Découpage terminé: {total_chunks} chunks créés")
        
        return all_chunks


# Fonctions utilitaires
def merge_chunks(chunks: List[Chunk], max_size: int = 1000) -> List[Chunk]:
    """
    Fusionne des chunks trop petits.
    
    Args:
        chunks: Liste de chunks à fusionner
        max_size: Taille maximale après fusion
        
    Returns:
        Liste de chunks fusionnés
    """
    if not chunks:
        return []
    
    merged_chunks = []
    current_chunk = chunks[0]
    
    for i in range(1, len(chunks)):
        next_chunk = chunks[i]
        
        # Vérifier si on peut fusionner
        merged_size = len(current_chunk.content) + len(next_chunk.content) + 1
        
        if (merged_size <= max_size and 
            current_chunk.metadata.get('source') == next_chunk.metadata.get('source')):
            
            # Fusionner les chunks
            merged_content = current_chunk.content + '\n' + next_chunk.content
            merged_metadata = current_chunk.metadata.copy()
            merged_metadata['chunk_size'] = len(merged_content)
            merged_metadata['word_count'] = len(merged_content.split())
            
            current_chunk = Chunk(
                content=merged_content,
                metadata=merged_metadata,
                chunk_id=f"{current_chunk.chunk_id}_merged",
                start_index=current_chunk.start_index,
                end_index=next_chunk.end_index
            )
        else:
            # Sauvegarder le chunk actuel et passer au suivant
            merged_chunks.append(current_chunk)
            current_chunk = next_chunk
    
    # Ajouter le dernier chunk
    merged_chunks.append(current_chunk)
    
    return merged_chunks


def filter_chunks(chunks: List[Chunk], min_words: int = 10, max_words: int = 1000) -> List[Chunk]:
    """
    Filtre les chunks selon des critères de qualité.
    
    Args:
        chunks: Liste de chunks à filtrer
        min_words: Nombre minimum de mots
        max_words: Nombre maximum de mots
        
    Returns:
        Liste de chunks filtrés
    """
    filtered_chunks = []
    
    for chunk in chunks:
        word_count = len(chunk.content.split())
        
        # Vérifier les critères
        if min_words <= word_count <= max_words:
            # Vérifier que le chunk n'est pas juste des espaces ou caractères spéciaux
            if chunk.content.strip() and len(chunk.content.strip()) > 20:
                filtered_chunks.append(chunk)
        else:
            logger.debug(f"Chunk filtré: {word_count} mots (critères: {min_words}-{max_words})")
    
    logger.info(f"Filtrage: {len(filtered_chunks)}/{len(chunks)} chunks conservés")
    return filtered_chunks 