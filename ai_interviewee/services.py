import os
import openai
import logging

logger = logging.getLogger(__name__)

class OpenAIEmbeddingService:
    """
    Service for generating embeddings using OpenAI's API.
    """
    def __init__(self, api_key=None, model="text-embedding-ada-002"):
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass it to the constructor.")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"OpenAIEmbeddingService initialized with model: {self.model}")

    def generate_embedding(self, text: str):
        """
        Generates an embedding for the given text using the specified OpenAI model.
        """
        if not text or not text.strip():
            logger.warning("Attempted to generate embedding for empty or whitespace-only text.")
            return None

        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            embedding = response.data[0].embedding
            logger.debug(f"Successfully generated embedding for text (first 50 chars): {text[:50]}...")
            return embedding
        except openai.APIError as e:
            logger.error(f"OpenAI API error during embedding generation: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during embedding generation: {e}")
            raise
