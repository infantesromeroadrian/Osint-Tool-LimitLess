import os
import re
import string
from typing import List, Dict, Any
import nltk
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from nltk.stem import WordNetLemmatizer
import PyPDF2
import pandas as pd
import docx

# Download required NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

class DocumentProcessor:
    """Processor for extracting, preprocessing, and chunking document text."""
    
    def __init__(self):
        """Initialize the document processor."""
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Load spaCy model only if needed
        self.nlp = None
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from various document formats.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content
        """
        print(f"DEBUG: Extracting text from file: {file_path}")
        
        if not os.path.exists(file_path):
            error_msg = f"File does not exist: {file_path}"
            print(f"DEBUG: ERROR - {error_msg}")
            raise FileNotFoundError(error_msg)
            
        file_extension = os.path.splitext(file_path)[1].lower()
        print(f"DEBUG: Detected file extension: {file_extension}")
        
        try:
            if file_extension == '.pdf':
                text = self._extract_from_pdf(file_path)
            elif file_extension == '.txt':
                text = self._extract_from_txt(file_path)
            elif file_extension == '.csv':
                text = self._extract_from_csv(file_path)
            elif file_extension == '.docx':
                text = self._extract_from_docx(file_path)
            else:
                error_msg = f"Unsupported file format: {file_extension}"
                print(f"DEBUG: ERROR - {error_msg}")
                raise ValueError(error_msg)
                
            # Check if text was successfully extracted
            if not text:
                print(f"DEBUG: WARNING - Extracted text is empty")
            else:
                print(f"DEBUG: Successfully extracted {len(text)} characters of text")
                
            return text
        except Exception as e:
            print(f"DEBUG: ERROR during text extraction: {str(e)}")
            import traceback
            print(f"DEBUG: Error traceback: {traceback.format_exc()}")
            raise
    
    def preprocess_text(self, text: str, options: List[str] = None) -> str:
        """Preprocess text with specified options.
        
        Args:
            text: Text to preprocess
            options: List of preprocessing options to apply
            
        Returns:
            Preprocessed text
        """
        if not options:
            options = ["Remove stopwords"]
        
        processed_text = text
        
        # Apply selected preprocessing options
        if "Remove stopwords" in options:
            processed_text = self._remove_stopwords(processed_text)
            
        if "Lemmatization" in options:
            processed_text = self._apply_lemmatization(processed_text)
            
        if "Named Entity Recognition" in options:
            processed_text = self._apply_ner(processed_text)
        
        return processed_text
    
    def split_text(
        self, 
        text: str, 
        chunk_size: int = 500, 
        chunk_overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks.
        
        Args:
            text: Text to split into chunks
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between consecutive chunks
            
        Returns:
            List of text chunks
        """
        # Check if text is empty
        if not text.strip():
            print(f"DEBUG: Cannot split empty text")
            return []
            
        # Split text into sentences
        print(f"DEBUG: Splitting text into sentences")
        sentences = sent_tokenize(text)
        print(f"DEBUG: Text split into {len(sentences)} sentences")
        
        # Initialize chunks
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # If adding this sentence exceeds chunk size, finalize current chunk
            if current_size + sentence_size > chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)
                print(f"DEBUG: Created chunk of size {len(chunk_text)}")
                
                # Keep overlap sentences for the next chunk
                overlap_start = max(0, len(current_chunk) - chunk_overlap // 10)
                current_chunk = current_chunk[overlap_start:]
                current_size = sum(len(s) for s in current_chunk)
            
            # Add the sentence to the current chunk
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add the last chunk if not empty
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
            print(f"DEBUG: Created final chunk of size {len(chunk_text)}")
        
        print(f"DEBUG: Created total of {len(chunks)} chunks")
        return chunks
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text
        """
        print(f"DEBUG: Extracting text from PDF: {file_path}")
        text = ""
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)
                print(f"DEBUG: PDF has {num_pages} pages")
                
                for page_num in range(num_pages):
                    page_text = pdf_reader.pages[page_num].extract_text()
                    if page_text:
                        text += page_text + "\n"
                        print(f"DEBUG: Extracted {len(page_text)} characters from page {page_num+1}")
                    else:
                        print(f"DEBUG: WARNING - No text extracted from page {page_num+1}")
                        
            # Check if any text was extracted
            if not text.strip():
                print(f"DEBUG: WARNING - No text could be extracted from PDF. This might be a scanned document or image-based PDF.")
                
            return text
        except Exception as e:
            print(f"DEBUG: ERROR extracting text from PDF: {str(e)}")
            import traceback
            print(f"DEBUG: Error traceback: {traceback.format_exc()}")
            raise
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from a plain text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Extracted text
        """
        print(f"DEBUG: Extracting text from TXT file: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as txt_file:
                text = txt_file.read()
                print(f"DEBUG: Extracted {len(text)} characters from text file")
                return text
        except Exception as e:
            print(f"DEBUG: ERROR extracting text from TXT file: {str(e)}")
            import traceback
            print(f"DEBUG: Error traceback: {traceback.format_exc()}")
            raise
    
    def _extract_from_csv(self, file_path: str) -> str:
        """Extract text from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Extracted text (concatenated rows)
        """
        print(f"DEBUG: Extracting text from CSV file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            text = df.to_string()
            print(f"DEBUG: Extracted {len(text)} characters from CSV file with {len(df)} rows")
            return text
        except Exception as e:
            print(f"DEBUG: ERROR extracting text from CSV file: {str(e)}")
            import traceback
            print(f"DEBUG: Error traceback: {traceback.format_exc()}")
            raise
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from a DOCX file.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            Extracted text
        """
        print(f"DEBUG: Extracting text from DOCX file: {file_path}")
        try:
            doc = docx.Document(file_path)
            paragraphs = [paragraph.text for paragraph in doc.paragraphs]
            text = "\n".join(paragraphs)
            
            print(f"DEBUG: Extracted {len(text)} characters from {len(paragraphs)} paragraphs in DOCX file")
            
            # Check if text was successfully extracted
            if not text.strip():
                print(f"DEBUG: WARNING - No text extracted from DOCX file")
                
            return text
        except Exception as e:
            print(f"DEBUG: ERROR extracting text from DOCX file: {str(e)}")
            import traceback
            print(f"DEBUG: Error traceback: {traceback.format_exc()}")
            raise
    
    def _remove_stopwords(self, text: str) -> str:
        """Remove stopwords from text.
        
        Args:
            text: Text to process
            
        Returns:
            Text with stopwords removed
        """
        words = text.split()
        filtered_words = [word for word in words if word.lower() not in self.stop_words]
        return " ".join(filtered_words)
    
    def _apply_lemmatization(self, text: str) -> str:
        """Apply lemmatization to text.
        
        Args:
            text: Text to lemmatize
            
        Returns:
            Lemmatized text
        """
        words = text.split()
        lemmatized_words = [self.lemmatizer.lemmatize(word) for word in words]
        return " ".join(lemmatized_words)
    
    def _apply_ner(self, text: str) -> str:
        """Apply Named Entity Recognition and enhance text with entity annotations.
        
        Args:
            text: Text to process
            
        Returns:
            Text with named entity annotations
        """
        # Load spaCy model if not already loaded
        if self.nlp is None:
            self.nlp = spacy.load("en_core_web_sm")
        
        doc = self.nlp(text)
        
        # Create a list of tokens with entity annotations
        tokens = []
        for token in doc:
            if token.ent_type_:
                tokens.append(f"{token.text}[{token.ent_type_}]")
            else:
                tokens.append(token.text)
        
        return " ".join(tokens) 