"""
Tests unitaires pour les modules d'ingestion de documents.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open

from ingestion.loaders import DocumentLoader
from ingestion.preprocess import DocumentPreprocessor
from ingestion.chunking import DocumentChunker


class TestDocumentLoader:
    """Tests pour le chargeur de documents."""
    
    def test_load_text_file(self, document_loader, temp_dir, sample_text):
        """Test de chargement d'un fichier texte."""
        # Créer un fichier texte temporaire
        text_file = os.path.join(temp_dir, "test.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(sample_text)
        
        # Charger le document
        document = document_loader.load_document(text_file)
        
        assert document is not None
        assert document['content'] == sample_text
        assert document['metadata']['filename'] == 'test.txt'
        assert document['metadata']['extension'] == '.txt'
        assert document['metadata']['size'] > 0
    
    def test_load_markdown_file(self, document_loader, temp_dir):
        """Test de chargement d'un fichier Markdown."""
        md_content = "# Titre\n\nCeci est un **texte en gras**."
        md_file = os.path.join(temp_dir, "test.md")
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        document = document_loader.load_document(md_file)
        
        assert document is not None
        assert document['content'] == md_content
        assert document['metadata']['filename'] == 'test.md'
        assert document['metadata']['extension'] == '.md'
    
    def test_load_unsupported_file(self, document_loader, temp_dir):
        """Test de chargement d'un fichier non supporté."""
        unsupported_file = os.path.join(temp_dir, "test.xyz")
        with open(unsupported_file, 'w') as f:
            f.write("contenu")
        
        with pytest.raises(ValueError, match="Type de fichier non supporté"):
            document_loader.load_document(unsupported_file)
    
    def test_load_nonexistent_file(self, document_loader):
        """Test de chargement d'un fichier inexistant."""
        with pytest.raises(FileNotFoundError):
            document_loader.load_document("fichier_inexistant.txt")
    
    @patch('PyPDF2.PdfReader')
    def test_load_pdf_file(self, mock_pdf_reader, document_loader, temp_dir):
        """Test de chargement d'un fichier PDF."""
        # Mock du contenu PDF
        mock_page = type('MockPage', (), {'extract_text': lambda: 'Contenu PDF'})()
        mock_pdf_reader.return_value.pages = [mock_page]
        
        pdf_file = os.path.join(temp_dir, "test.pdf")
        with open(pdf_file, 'wb') as f:
            f.write(b"PDF content")
        
        document = document_loader.load_document(pdf_file)
        
        assert document is not None
        assert document['content'] == 'Contenu PDF'
        assert document['metadata']['filename'] == 'test.pdf'
        assert document['metadata']['extension'] == '.pdf'
    
    def test_get_file_info(self, document_loader, temp_dir, sample_text):
        """Test de récupération des informations de fichier."""
        text_file = os.path.join(temp_dir, "test.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(sample_text)
        
        info = document_loader.get_file_info(text_file)
        
        assert info['filename'] == 'test.txt'
        assert info['extension'] == '.txt'
        assert info['size'] > 0
        assert 'created_at' in info
        assert 'modified_at' in info
    
    def test_validate_file_valid(self, document_loader, temp_dir):
        """Test de validation d'un fichier valide."""
        text_file = os.path.join(temp_dir, "test.txt")
        with open(text_file, 'w') as f:
            f.write("contenu")
        
        assert document_loader.validate_file(text_file) is True
    
    def test_validate_file_invalid(self, document_loader):
        """Test de validation d'un fichier invalide."""
        assert document_loader.validate_file("fichier_inexistant.txt") is False
        assert document_loader.validate_file("") is False


class TestDocumentPreprocessor:
    """Tests pour le préprocesseur de documents."""
    
    def test_preprocess_document(self, document_preprocessor):
        """Test de prétraitement d'un document."""
        document = {
            'content': '  Texte avec    espaces   multiples.\n\n\nEt lignes vides.  \n\n',
            'metadata': {'filename': 'test.txt'}
        }
        
        processed = document_preprocessor.preprocess_document(document)
        
        assert processed['content'] == 'Texte avec espaces multiples.\n\nEt lignes vides.'
        assert processed['metadata']['processed'] is True
        assert processed['metadata']['word_count'] > 0
        assert processed['metadata']['char_count'] > 0
    
    def test_clean_text(self, document_preprocessor):
        """Test de nettoyage du texte."""
        dirty_text = "  Texte avec    espaces   multiples.\n\n\n\nEt lignes vides.  \n\n"
        
        clean_text = document_preprocessor.clean_text(dirty_text)
        
        assert clean_text == "Texte avec espaces multiples.\n\nEt lignes vides."
    
    def test_normalize_text(self, document_preprocessor):
        """Test de normalisation du texte."""
        text = "TEXTE en MAJUSCULES et minuscules"
        
        normalized = document_preprocessor.normalize_text(text)
        
        # La normalisation peut varier selon l'implémentation
        assert len(normalized) > 0
        assert isinstance(normalized, str)
    
    def test_extract_metadata(self, document_preprocessor, sample_text):
        """Test d'extraction de métadonnées."""
        metadata = document_preprocessor.extract_metadata(sample_text)
        
        assert 'word_count' in metadata
        assert 'char_count' in metadata
        assert 'line_count' in metadata
        assert metadata['word_count'] > 0
        assert metadata['char_count'] > 0
        assert metadata['line_count'] > 0
    
    def test_remove_extra_whitespace(self, document_preprocessor):
        """Test de suppression des espaces en trop."""
        text = "Texte  avec    espaces   multiples"
        
        result = document_preprocessor.remove_extra_whitespace(text)
        
        assert result == "Texte avec espaces multiples"
    
    def test_remove_empty_lines(self, document_preprocessor):
        """Test de suppression des lignes vides."""
        text = "Ligne 1\n\n\n\nLigne 2\n\n\nLigne 3"
        
        result = document_preprocessor.remove_empty_lines(text)
        
        assert result == "Ligne 1\n\nLigne 2\n\nLigne 3"


class TestDocumentChunker:
    """Tests pour le découpage de documents."""
    
    def test_chunk_document(self, document_chunker):
        """Test de découpage d'un document."""
        document = {
            'content': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 10,
            'metadata': {'filename': 'test.txt'}
        }
        
        chunks = document_chunker.chunk_document(document)
        
        assert len(chunks) > 0
        assert all('chunk_id' in chunk for chunk in chunks)
        assert all('content' in chunk for chunk in chunks)
        assert all('metadata' in chunk for chunk in chunks)
        assert all(len(chunk['content']) <= document_chunker.chunk_size + 50 for chunk in chunks)
    
    def test_chunk_by_size(self, document_chunker):
        """Test de découpage par taille."""
        text = "mot " * 50  # 200 caractères environ
        
        chunks = document_chunker._chunk_by_size(text)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= document_chunker.chunk_size + document_chunker.chunk_overlap for chunk in chunks)
    
    def test_chunk_by_structure(self, document_chunker):
        """Test de découpage par structure."""
        text = """# Titre 1

Paragraphe 1 avec du contenu.

## Sous-titre 1.1

Paragraphe 2 avec plus de contenu.

# Titre 2

Paragraphe 3 avec encore du contenu."""
        
        chunks = document_chunker._chunk_by_structure(text)
        
        assert len(chunks) > 0
        # Vérifier que les chunks contiennent des sections logiques
        assert any('Titre 1' in chunk for chunk in chunks)
        assert any('Titre 2' in chunk for chunk in chunks)
    
    def test_ensure_chunk_size(self, document_chunker):
        """Test de vérification de la taille des chunks."""
        long_chunk = "mot " * 200  # Chunk trop long
        
        chunks = document_chunker._ensure_chunk_size(long_chunk)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= document_chunker.chunk_size + 50 for chunk in chunks)
    
    def test_add_chunk_metadata(self, document_chunker):
        """Test d'ajout de métadonnées aux chunks."""
        chunks = ['chunk 1', 'chunk 2', 'chunk 3']
        document_metadata = {'filename': 'test.txt', 'author': 'Test'}
        
        result = document_chunker._add_chunk_metadata(chunks, document_metadata)
        
        assert len(result) == 3
        for i, chunk_obj in enumerate(result):
            assert chunk_obj['chunk_id'].startswith('chunk_')
            assert chunk_obj['content'] == chunks[i]
            assert chunk_obj['metadata']['filename'] == 'test.txt'
            assert chunk_obj['metadata']['author'] == 'Test'
            assert chunk_obj['metadata']['chunk_index'] == i
    
    def test_split_sentences(self, document_chunker):
        """Test de division en phrases."""
        text = "Première phrase. Deuxième phrase! Troisième phrase?"
        
        sentences = document_chunker._split_sentences(text)
        
        assert len(sentences) == 3
        assert sentences[0] == "Première phrase."
        assert sentences[1] == "Deuxième phrase!"
        assert sentences[2] == "Troisième phrase?"
    
    def test_empty_document(self, document_chunker):
        """Test avec un document vide."""
        document = {
            'content': '',
            'metadata': {'filename': 'empty.txt'}
        }
        
        chunks = document_chunker.chunk_document(document)
        
        assert len(chunks) == 0
    
    def test_small_document(self, document_chunker):
        """Test avec un petit document."""
        document = {
            'content': 'Petit document.',
            'metadata': {'filename': 'small.txt'}
        }
        
        chunks = document_chunker.chunk_document(document)
        
        assert len(chunks) == 1
        assert chunks[0]['content'] == 'Petit document.'


# Tests d'intégration
class TestIngestionIntegration:
    """Tests d'intégration pour le pipeline d'ingestion."""
    
    def test_full_pipeline(self, temp_dir, sample_text):
        """Test du pipeline complet d'ingestion."""
        # Créer un fichier de test
        text_file = os.path.join(temp_dir, "integration_test.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(sample_text)
        
        # Étape 1: Chargement
        loader = DocumentLoader()
        document = loader.load_document(text_file)
        
        # Étape 2: Prétraitement
        preprocessor = DocumentPreprocessor()
        processed_doc = preprocessor.preprocess_document(document)
        
        # Étape 3: Découpage
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=50)
        chunks = chunker.chunk_document(processed_doc)
        
        # Vérifications
        assert document is not None
        assert processed_doc is not None
        assert len(chunks) > 0
        assert all('chunk_id' in chunk for chunk in chunks)
        assert all('content' in chunk for chunk in chunks)
        assert all('metadata' in chunk for chunk in chunks)
        
        # Vérifier que le contenu est préservé
        total_content = ' '.join(chunk['content'] for chunk in chunks)
        assert 'intelligence artificielle' in total_content.lower()
        assert 'apprentissage automatique' in total_content.lower() 