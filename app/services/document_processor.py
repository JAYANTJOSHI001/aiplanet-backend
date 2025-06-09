import os
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any
from pydantic import PrivateAttr

from dotenv import load_dotenv
from llama_index.core.settings import Settings

from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    Document,
)
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores.simple import SimpleVectorStore
from llama_index.core.llms import CustomLLM
from llama_index.core.llms import CompletionResponse, LLMMetadata
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Set Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create a custom LLM class for Gemini
class GeminiLLM(CustomLLM):
    _model: Any = PrivateAttr()

    def __init__(self):
        super().__init__()
        # Configure the Gemini model
        self._model = genai.GenerativeModel('gemini-1.5-flash')
    
    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            model_name="gemini-1.5-flash",
            max_input_size=30720,
            num_output=8192,
            context_window=30720,
        )
    
    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        try:
            response = self._model.generate_content(prompt)
            return CompletionResponse(text=response.text)
        except Exception as e:
            print(f"Error with Gemini API: {e}")
            return CompletionResponse(text="Error generating response")
    
    def stream_complete(self, prompt: str, **kwargs):
        response = self.complete(prompt, **kwargs)
        yield response

# Initialize the Gemini LLM
gemini_llm = GeminiLLM()

Settings.llm = gemini_llm

Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

UPLOAD_DIR = Path("uploads")
INDEX_DIR = Path("indices")

class DocumentProcessor:
    def __init__(self):
        self.upload_dir = UPLOAD_DIR
        self.index_dir = INDEX_DIR
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(exist_ok=True)
        self.index_dir.mkdir(exist_ok=True)
    
    def save_pdf(self, file_content: bytes, filename: str) -> str:
        """Save uploaded PDF file to disk"""
        filepath = self.upload_dir / filename
        with open(filepath, "wb") as f:
            f.write(file_content)
        return str(filepath)
    
    def extract_text(self, filepath: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            print(f"Attempting to open PDF at: {filepath}")
            pdf_document = fitz.open(filepath)
            print(f"PDF opened successfully. Page count: {pdf_document.page_count}")
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                page_text = page.get_text()
                text += page_text
                print(f"Extracted {len(page_text)} characters from page {page_num+1}")
                
            pdf_document.close()
            
            if not text.strip():
                print(f"Warning: Extracted text is empty or contains only whitespace")
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"Total extracted text length: {len(text)}")
        return text
    
    def create_index(self, document_id: int, filepath: str) -> bool:
        """Create a searchable index from the PDF content"""
        try:
            # Extract text from PDF
            text = self.extract_text(filepath)
            
            if not text or not text.strip():
                print(f"No text extracted from document {document_id}")
                # Try to diagnose the issue
                try:
                    import os
                    if not os.path.exists(filepath):
                        print(f"File does not exist at path: {filepath}")
                    else:
                        file_size = os.path.getsize(filepath)
                        print(f"File exists, size: {file_size} bytes")
                        
                        # Check if file is readable
                        with open(filepath, 'rb') as f:
                            first_bytes = f.read(10)
                        print(f"First bytes of file: {first_bytes}")
                except Exception as diag_error:
                    print(f"Error during diagnosis: {diag_error}")
                    
                    return False
                    
            # Create a Document object for llama-index
            documents = [Document(text=text)]
            
            # Create storage context
            storage_context = StorageContext.from_defaults(
                docstore=SimpleDocumentStore(),
                vector_store=SimpleVectorStore(),
                index_store=SimpleIndexStore(),
            )
            
            # Create index with Gemini LLM
            index = VectorStoreIndex.from_documents(  # Changed from GPTVectorStoreIndex
                documents, 
                storage_context=storage_context,
            )
            
            # Save index
            index_path = self.index_dir / f"index_{document_id}"
            # Remove existing index if it exists
            if index_path.exists():
                import shutil
                shutil.rmtree(index_path)
            
            index_path.mkdir(exist_ok=True)
            index.storage_context.persist(persist_dir=str(index_path))
            
            # Verify index was created
            docstore_path = index_path / "docstore.json"
            if not docstore_path.exists():
                print(f"Index files not created properly for document {document_id}")
                return False
                
            return True
        except Exception as e:
            print(f"Error creating index: {e}")
            return False