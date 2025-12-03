"""
Module de chargement des documents depuis différents formats.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import PyPDF2
from docx import Document
import markdown
from unstructured.documents.elements import Title, NarrativeText
from unstructured.partition.auto import partition

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Charge différents types de documents."""
    
    def __init__(self):
        self.supported_extensions = {
            '.pdf': self._load_pdf,
            '.txt': self._load_text,
            '.md': self._load_markdown,
            '.docx': self._load_docx,
        }
    
    def load_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Charge un document depuis un fichier.
        
        Args:
            file_path: Chemin vers le fichier
            metadata: Métadonnées additionnelles
            
        Returns:
            Dictionnaire contenant le contenu et les métadonnées
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
        
        extension = file_path.suffix.lower()
        
        if extension not in self.supported_extensions:
            raise ValueError(f"Extension {extension} non supportée. "
                           f"Extensions supportées: {list(self.supported_extensions.keys())}")
        
        try:
            content = self.supported_extensions[extension](file_path)
            
            document_metadata = {
                'source': str(file_path),
                'filename': file_path.name,
                'extension': extension,
                'size': file_path.stat().st_size,
                'created_at': file_path.stat().st_ctime,
                'modified_at': file_path.stat().st_mtime,
            }
            
            if metadata:
                document_metadata.update(metadata)
            
            return {
                'content': content,
                'metadata': document_metadata
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {file_path}: {e}")
            raise
    
    def load_directory(self, directory_path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Charge tous les documents d'un répertoire.
        
        Args:
            directory_path: Chemin vers le répertoire
            recursive: Si True, explore les sous-répertoires
            
        Returns:
            Liste des documents chargés
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Le répertoire {directory_path} n'existe pas")
        
        documents = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory_path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                try:
                    doc = self.load_document(str(file_path))
                    documents.append(doc)
                    logger.info(f"Document chargé: {file_path}")
                except Exception as e:
                    logger.warning(f"Impossible de charger {file_path}: {e}")
        
        logger.info(f"Chargement terminé: {len(documents)} documents")
        return documents
    
    def _load_pdf(self, file_path: Path) -> str:
        """Charge un fichier PDF."""
        content = ""
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            content += f"\n--- Page {page_num + 1} ---\n"
                            content += page_text
                    except Exception as e:
                        logger.warning(f"Erreur page {page_num + 1} dans {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du PDF {file_path}: {e}")
            # Fallback avec unstructured
            try:
                elements = partition(filename=str(file_path))
                content = "\n".join([str(element) for element in elements])
            except:
                raise e
        
        return content.strip()
    
    def _load_text(self, file_path: Path) -> str:
        """Charge un fichier texte."""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        
        raise UnicodeDecodeError(f"Impossible de décoder {file_path} avec les encodages: {encodings}")
    
    def _load_markdown(self, file_path: Path) -> str:
        """Charge un fichier Markdown."""
        with open(file_path, 'r', encoding='utf-8') as file:
            md_content = file.read()
        
        # Convertir en HTML puis extraire le texte
        html = markdown.markdown(md_content)
        
        # Simple extraction du texte (on pourrait utiliser BeautifulSoup pour plus de sophistication)
        import re
        text = re.sub(r'<[^>]+>', '', html)
        return text.strip()
    
    def _load_docx(self, file_path: Path) -> str:
        """Charge un fichier Word."""
        doc = Document(file_path)
        content = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text.strip())
        
        return "\n".join(content)


# Fonctions utilitaires
def get_file_info(file_path: str) -> Dict[str, Any]:
    """Récupère les informations d'un fichier."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
    
    stat = file_path.stat()
    
    return {
        'name': file_path.name,
        'path': str(file_path),
        'size': stat.st_size,
        'extension': file_path.suffix,
        'created_at': stat.st_ctime,
        'modified_at': stat.st_mtime,
        'is_file': file_path.is_file(),
        'is_dir': file_path.is_dir(),
    }


def validate_file(file_path: str, max_size: int = 10485760) -> bool:
    """
    Valide un fichier avant chargement.
    
    Args:
        file_path: Chemin vers le fichier
        max_size: Taille maximale en bytes (défaut: 10MB)
        
    Returns:
        True si le fichier est valide
    """
    try:
        info = get_file_info(file_path)
        
        if not info['is_file']:
            return False
        
        if info['size'] > max_size:
            logger.warning(f"Fichier trop volumineux: {info['size']} > {max_size}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la validation de {file_path}: {e}")
        return False 