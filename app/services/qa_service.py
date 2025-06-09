from pathlib import Path
from llama_index.core import (
    StorageContext,
    load_index_from_storage,
    ServiceContext,
    VectorStoreIndex,
)

from typing import Any

from pydantic import PrivateAttr
import os
from dotenv import load_dotenv
from llama_index.core.settings import Settings

import google.generativeai as genai
from llama_index.core.llms import CompletionResponse, LLMMetadata
from llama_index.core.llms import CustomLLM

from llama_index.core.llms import ChatMessage

from llama_index.core.llms import CompletionResponse, LLMMetadata

# Load environment variables from .env file
load_dotenv()

# Set Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create a custom LLM class for Gemini
class GeminiLLM(CustomLLM):
    _model: Any = PrivateAttr()

    def __init__(self):
        super().__init__()
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


INDEX_DIR = Path("indices")

class QAService:
    def __init__(self):
        self.index_dir = INDEX_DIR
    
    def get_answer(self, document_id: int, question: str) -> str:
        """Get answer to a question based on document content"""
        try:
            # Check if index exists
            index_path = self.index_dir / f"index_{document_id}"
            
            # Verify if the index files exist
            docstore_path = index_path / "docstore.json"
            if not os.path.exists(docstore_path):
                return "Sorry, the index for this document appears to be missing or corrupted. Please try re-uploading the document."
            
            # Load the index for the document
            storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
            index = load_index_from_storage(storage_context)
            
            # Create query engine
            query_engine = index.as_query_engine()
            
            # Get response
            response = query_engine.query(question)
            
            return str(response)
        except Exception as e:
            print(f"Error getting answer: {e}")
            return f"Sorry, I couldn't process your question. Error: {str(e)}"