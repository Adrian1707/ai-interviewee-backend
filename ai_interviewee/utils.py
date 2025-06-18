import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(file_path):
    """
    Extract text from various file formats
    """
    file_extension = Path(file_path).suffix.lower()
    
    try:
        if file_extension == '.pdf':
            return extract_text_from_pdf(file_path)
        elif file_extension == '.txt':
            return extract_text_from_txt(file_path)
        elif file_extension in ['.doc', '.docx']:
            return extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        raise


def extract_text_from_pdf(file_path):
    """
    Extract text from PDF using pdfminer.six
    """
    try:
        from pdfminer.high_level import extract_text
        return extract_text(file_path)
    except ImportError:
        logger.error("pdfminer.six not installed. Install with: pip install pdfminer.six")
        raise
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        raise


def extract_text_from_txt(file_path):
    """
    Extract text from TXT file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e2:
            logger.error(f"Error extracting text from TXT {file_path}: {str(e2)}")
            raise


def extract_text_from_docx(file_path):
    """
    Extract text from DOCX using python-docx
    """
    try:
        from docx import Document
        doc = Document(file_path)
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    except ImportError:
        logger.error("python-docx not installed. Install with: pip install python-docx")
        raise
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
        raise


def chunk_text(text, chunk_size=300, overlap=50):
    """
    Split text into chunks with overlap
    
    Args:
        text (str): The text to chunk
        chunk_size (int): Target number of words per chunk
        overlap (int): Number of words to overlap between chunks
    
    Returns:
        List of chunk dictionaries
    """
    if not text or not text.strip():
        return []
    
    words = text.split()
    chunks = []
    
    if len(words) <= chunk_size:
        # If text is shorter than chunk size, return as single chunk
        return [{
            'content': text.strip(),
            'start_char': 0,
            'end_char': len(text),
            'metadata': {'word_count': len(words)}
        }]
    
    start_idx = 0
    chunk_index = 0
    
    while start_idx < len(words):
        # Calculate end index for this chunk
        end_idx = min(start_idx + chunk_size, len(words))
        
        # Extract chunk words
        chunk_words = words[start_idx:end_idx]
        chunk_content = ' '.join(chunk_words)
        
        # Calculate character positions (approximate)
        start_char = len(' '.join(words[:start_idx]))
        if start_idx > 0:
            start_char += 1  # Add space before chunk
        end_char = start_char + len(chunk_content)
        
        # Create chunk data
        chunk_data = {
            'content': chunk_content.strip(),
            'start_char': start_char,
            'end_char': end_char,
            'metadata': {
                'word_count': len(chunk_words),
                'chunk_index': chunk_index
            }
        }
        
        chunks.append(chunk_data)
        
        # Move to next chunk with overlap
        if end_idx >= len(words):
            break
        
        start_idx = max(start_idx + chunk_size - overlap, start_idx + 1)
        chunk_index += 1
    
    logger.info(f"Created {len(chunks)} chunks from {len(words)} words")
    return chunks
