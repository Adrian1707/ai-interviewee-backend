import pytest
import os
from unittest.mock import patch, mock_open
from pathlib import Path
from ai_interviewee.utils import (
    extract_text_from_file,
    extract_text_from_pdf,
    extract_text_from_txt,
    extract_text_from_docx,
    chunk_text
)

# --- Fixtures for dummy files ---

@pytest.fixture
def dummy_pdf_file(tmp_path):
    file_path = tmp_path / "dummy.pdf"
    # In a real scenario, you might create a minimal PDF or mock the PDF content
    file_path.write_text("This is a dummy PDF content.")
    return file_path

@pytest.fixture
def dummy_txt_file(tmp_path):
    file_path = tmp_path / "dummy.txt"
    file_path.write_text("This is a dummy TXT content.")
    return file_path

@pytest.fixture
def dummy_docx_file(tmp_path):
    file_path = tmp_path / "dummy.docx"
    # In a real scenario, you might create a minimal DOCX or mock the DOCX content
    file_path.write_text("This is a dummy DOCX content.")
    return file_path

# --- Tests for extract_text_from_pdf ---

@patch('pdfminer.high_level.extract_text')
def test_extract_text_from_pdf_success(mock_extract_text, dummy_pdf_file):
    mock_extract_text.return_value = "Text from PDF"
    result = extract_text_from_pdf(dummy_pdf_file)
    assert result == "Text from PDF"
    mock_extract_text.assert_called_once_with(dummy_pdf_file)

@patch('pdfminer.high_level.extract_text', side_effect=ImportError)
def test_extract_text_from_pdf_import_error(mock_extract_text, dummy_pdf_file):
    with pytest.raises(ImportError):
        extract_text_from_pdf(dummy_pdf_file)

@patch('pdfminer.high_level.extract_text', side_effect=Exception("PDF error"))
def test_extract_text_from_pdf_general_error(mock_extract_text, dummy_pdf_file):
    with pytest.raises(Exception, match="PDF error"):
        extract_text_from_pdf(dummy_pdf_file)

# --- Tests for extract_text_from_txt ---

@patch("builtins.open", new_callable=mock_open, read_data="Text from TXT")
def test_extract_text_from_txt_success(mock_file, dummy_txt_file):
    result = extract_text_from_txt(dummy_txt_file)
    assert result == "Text from TXT"
    mock_file.assert_called_once_with(dummy_txt_file, 'r', encoding='utf-8')

@patch("builtins.open", side_effect=[Exception("UTF-8 error"), mock_open(read_data="Text from TXT latin-1").return_value])
def test_extract_text_from_txt_encoding_fallback(mock_file, dummy_txt_file):
    result = extract_text_from_txt(dummy_txt_file)
    assert result == "Text from TXT latin-1"
    assert mock_file.call_count == 2

@patch("builtins.open", side_effect=Exception("File error"))
def test_extract_text_from_txt_general_error(mock_file, dummy_txt_file):
    with pytest.raises(Exception, match="File error"):
        extract_text_from_txt(dummy_txt_file)

# --- Tests for extract_text_from_docx ---

@patch('docx.Document')
def test_extract_text_from_docx_success(mock_document, dummy_docx_file):
    mock_doc_instance = mock_document.return_value
    mock_doc_instance.paragraphs = [
        type('obj', (object,), {'text': 'Paragraph 1'})(),
        type('obj', (object,), {'text': 'Paragraph 2'})()
    ]
    result = extract_text_from_docx(dummy_docx_file)
    assert result == "Paragraph 1\nParagraph 2"
    mock_document.assert_called_once_with(dummy_docx_file)

@patch('docx.Document', side_effect=ImportError)
def test_extract_text_from_docx_import_error(mock_document, dummy_docx_file):
    with pytest.raises(ImportError):
        extract_text_from_docx(dummy_docx_file)

@patch('docx.Document', side_effect=Exception("DOCX error"))
def test_extract_text_from_docx_general_error(mock_document, dummy_docx_file):
    with pytest.raises(Exception, match="DOCX error"):
        extract_text_from_docx(dummy_docx_file)

# --- Tests for extract_text_from_file ---

@patch('ai_interviewee.utils.extract_text_from_pdf')
def test_extract_text_from_file_pdf(mock_extract_pdf, tmp_path):
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("dummy") # Content doesn't matter for this mock
    mock_extract_pdf.return_value = "PDF Content"
    result = extract_text_from_file(pdf_file)
    assert result == "PDF Content"
    mock_extract_pdf.assert_called_once_with(pdf_file)

@patch('ai_interviewee.utils.extract_text_from_txt')
def test_extract_text_from_file_txt(mock_extract_txt, tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("dummy")
    mock_extract_txt.return_value = "TXT Content"
    result = extract_text_from_file(txt_file)
    assert result == "TXT Content"
    mock_extract_txt.assert_called_once_with(txt_file)

@patch('ai_interviewee.utils.extract_text_from_docx')
def test_extract_text_from_file_docx(mock_extract_docx, tmp_path):
    docx_file = tmp_path / "test.docx"
    docx_file.write_text("dummy")
    mock_extract_docx.return_value = "DOCX Content"
    result = extract_text_from_file(docx_file)
    assert result == "DOCX Content"
    mock_extract_docx.assert_called_once_with(docx_file)

def test_extract_text_from_file_unsupported_format(tmp_path):
    unsupported_file = tmp_path / "test.jpg"
    unsupported_file.write_text("dummy")
    with pytest.raises(ValueError, match="Unsupported file format: .jpg"):
        extract_text_from_file(unsupported_file)

@patch('ai_interviewee.utils.extract_text_from_pdf', side_effect=Exception("Extraction failed"))
def test_extract_text_from_file_error_handling(mock_extract_pdf, tmp_path):
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("dummy")
    with pytest.raises(Exception, match="Extraction failed"):
        extract_text_from_file(pdf_file)

# --- Tests for chunk_text ---

def test_chunk_text_empty_input():
    assert chunk_text("") == []
    assert chunk_text("   ") == []
    assert chunk_text(None) == []

def test_chunk_text_short_text_single_chunk():
    text = "This is a short text."
    chunks = chunk_text(text, chunk_size=10, overlap=2)
    assert len(chunks) == 1
    assert chunks[0]['content'] == text
    assert chunks[0]['start_char'] == 0
    assert chunks[0]['end_char'] == len(text)
    assert chunks[0]['metadata']['word_count'] == len(text.split())

def test_chunk_text_multiple_chunks_no_overlap():
    text = "This is a longer text that needs to be split into multiple chunks for processing."
    chunks = chunk_text(text, chunk_size=5, overlap=0)
    assert len(chunks) == 3
    assert chunks[0]['content'] == "This is a longer text"
    assert chunks[1]['content'] == "that needs to be split"
    assert chunks[2]['content'] == "into multiple chunks for processing."

def test_chunk_text_multiple_chunks_with_overlap():
    text = "The quick brown fox jumps over the lazy dog. This is another sentence."
    chunks = chunk_text(text, chunk_size=5, overlap=2)
    assert len(chunks) == 4
    assert chunks[0]['content'] == "The quick brown fox jumps"
    assert chunks[1]['content'] == "fox jumps over the lazy"
    assert chunks[2]['content'] == "the lazy dog. This is"
    assert chunks[3]['content'] == "This is another sentence."

def test_chunk_text_exact_chunk_size():
    text = "One two three four five six seven eight nine ten"
    chunks = chunk_text(text, chunk_size=5, overlap=0)
    assert len(chunks) == 2
    assert chunks[0]['content'] == "One two three four five"
    assert chunks[1]['content'] == "six seven eight nine ten"

def test_chunk_text_large_overlap():
    text = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z"
    chunks = chunk_text(text, chunk_size=5, overlap=4)
    assert len(chunks) == 22 # Corrected from 6
    assert chunks[0]['content'] == "A B C D E"
    assert chunks[1]['content'] == "B C D E F"
    assert chunks[2]['content'] == "C D E F G"
    assert chunks[3]['content'] == "D E F G H"
    assert chunks[4]['content'] == "E F G H I"
    assert chunks[5]['content'] == "F G H I J"
    assert chunks[21]['content'] == "V W X Y Z" # Added assertion for the last chunk

def test_chunk_text_character_positions():
    text = "Word1 Word2 Word3 Word4 Word5 Word6"
    chunks = chunk_text(text, chunk_size=2, overlap=1)
    
    # Chunk 1: "Word1 Word2"
    assert chunks[0]['content'] == "Word1 Word2"
    assert chunks[0]['start_char'] == 0
    assert chunks[0]['end_char'] == len("Word1 Word2")

    # Chunk 2: "Word2 Word3" (overlap on Word2)
    assert chunks[1]['content'] == "Word2 Word3"
    assert chunks[1]['start_char'] == len("Word1 ")
    assert chunks[1]['end_char'] == 17 # Corrected from len("Word1 Word2 Word3") - len(" Word1")

    # Chunk 3: "Word3 Word4"
    assert chunks[2]['content'] == "Word3 Word4"
    assert chunks[2]['start_char'] == 12 # Corrected from len("Word1 Word2 ")
    assert chunks[2]['end_char'] == 23 # Corrected from len("Word1 Word2 Word3 Word4") - len(" Word1 Word2")

    # Chunk 4: "Word4 Word5"
    assert chunks[3]['content'] == "Word4 Word5"
    assert chunks[3]['start_char'] == 18 # Corrected from len("Word1 Word2 Word3 ")
    assert chunks[3]['end_char'] == 29 # Corrected from len("Word1 Word2 Word3 Word4 Word5") - len(" Word1 Word2 Word3")

    # Chunk 5: "Word5 Word6"
    assert chunks[4]['content'] == "Word5 Word6"
    assert chunks[4]['start_char'] == 24 # Corrected from len("Word1 Word2 Word3 Word4 ")
    assert chunks[4]['end_char'] == 35 # Corrected from len("Word1 Word2 Word3 Word4 Word5 Word6") - len(" Word1 Word2 Word3 Word4")

def test_chunk_text_single_word_chunk_size():
    text = "One Two Three Four Five"
    chunks = chunk_text(text, chunk_size=1, overlap=0)
    assert len(chunks) == 5
    assert chunks[0]['content'] == "One"
    assert chunks[1]['content'] == "Two"

def test_chunk_text_overlap_greater_than_chunk_size():
    text = "This is a test sentence."
    chunks = chunk_text(text, chunk_size=3, overlap=5) # Overlap > chunk_size, should still work
    assert len(chunks) == 3
    assert chunks[0]['content'] == "This is a"
    assert chunks[1]['content'] == "is a test"
    assert chunks[2]['content'] == "a test sentence."
