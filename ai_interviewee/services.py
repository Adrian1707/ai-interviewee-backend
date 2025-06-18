import os
import openai
import logging
from django.conf import settings
from django.db.models import F
from .models import DocumentChunk, Persona

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

class RagService:
    """
    Service for Retrieval-Augmented Generation (RAG) using OpenAI and Django-pgvector.
    """
    def __init__(self):
        self.embedding_service = OpenAIEmbeddingService(api_key=settings.OPENAI_API_KEY)
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.chat_model = "gpt-3.5-turbo" # Or gpt-4, depending on preference/availability

    def call(self, question: str, persona: Persona) -> str:
        """
        Performs RAG logic to answer a question based on retrieved document chunks.
        """
        if not question or not persona:
            raise ValueError("Question and Persona must be provided.")

        # 1. Get the question's embedding
        question_embedding = self.embedding_service.generate_embedding(question)
        if question_embedding is None:
            logger.error("Failed to generate embedding for the question.")
            return "Error: Could not process the question."

        # 2. Query for the most similar DocumentChunk records
        try:
            # Ensure question_embedding is a list of floats for l2_distance
            if not isinstance(question_embedding, list):
                question_embedding = list(question_embedding)

            similar_chunks = DocumentChunk.objects.filter(persona=persona).order_by(
                F('embedding').l2_distance(question_embedding)
            ).limit(5)
            
            context_chunks = [chunk.content for chunk in similar_chunks]
            logger.debug(f"Retrieved {len(context_chunks)} similar document chunks for persona {persona.name}.")
        except Exception as e:
            logger.error(f"Error querying similar document chunks: {e}")
            return "Error: Could not retrieve relevant information."

        # 3. Build the detailed system prompt with the retrieved context chunks
        system_prompt = (
            f"You are an AI assistant that embodies the professional persona of {persona.name}.\n"
            "Your purpose is to answer questions from a potential interviewer based *strictly* and *exclusively* on the context provided below.\n\n"
            "Do not use any outside knowledge. Do not infer or invent information that is not explicitly stated in the context.\n"

            "If the provided context does not contain the answer to the question, you MUST respond with one of the following phrases:\n"
            "- \"I don't have specific details on that in the documents I've been provided with.\"\n"
            "- \"That topic isn't covered in the experience I have on file.\"\n"
            "- \"I can't answer that question based on the information available to me.\"\n\n"
            
            f"Answer from a first-person perspective, as if you are {persona.name}. Be professional, concise, and helpful.\n\n"
            "---\n"
            "CONTEXT:\n" + "\n".join(context_chunks) + "\n"
            "---\n\n"
            "INTERVIEWER's QUESTION:\n" + question
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]

        # 4. Call the OpenAI Chat Completions API
        try:
            chat_completion = self.openai_client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=0.7, # Adjust as needed for creativity vs. factualness
                max_tokens=500 # Limit response length
            )
            ai_response = chat_completion.choices[0].message.content
            logger.info("Successfully generated AI response.")
            return ai_response
        except openai.APIError as e:
            logger.error(f"OpenAI API error during chat completion: {e}")
            return "Error: Failed to get a response from the AI."
        except Exception as e:
            logger.error(f"An unexpected error occurred during chat completion: {e}")
            return "Error: An unexpected error occurred."
