import os
import logging
from typing import Optional, List, Union

import openai

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService:
    """
    Service for generating embeddings using OpenAI's API.
    
    This service provides a clean interface for generating text embeddings
    using OpenAI's embedding models with proper error handling and logging.
    
    Args:
        api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
        model: The embedding model to use. Defaults to text-embedding-3-small.
        
    Raises:
        ValueError: If no API key is provided via parameter or environment variable.
    """
    
    # Class constant for default model
    DEFAULT_MODEL = "text-embedding-3-small"
    
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL) -> None:
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment "
                "variable or pass it to the constructor."
            )
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        logger.info("OpenAIEmbeddingService initialized with model: %s", self.model)

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate an embedding for the given text using the specified OpenAI model.
        
        Args:
            text: The input text to generate embeddings for.
            
        Returns:
            A list of floats representing the embedding vector, or None if input is invalid.
            
        Raises:
            openai.APIError: If there's an API-related error.
            Exception: For other unexpected errors during embedding generation.
        """
        if not text or not text.strip():
            logger.warning("Attempted to generate embedding for empty or whitespace-only text")
            return None

        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            embedding = response.data[0].embedding
            logger.debug(
                "Successfully generated embedding for text (first 50 chars): %s...", 
                text[:50]
            )
            return embedding
            
        except openai.APIError as e:
            logger.error("OpenAI API error during embedding generation: %s", e)
            raise
        except Exception as e:
            logger.error("Unexpected error during embedding generation: %s", e)
            raise
