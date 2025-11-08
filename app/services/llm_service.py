"""LLM service using Google Gemini API with ADK integration."""

import logging
from typing import Any

from google import genai
from google.genai import types

from app.config.config import get_settings
from app.infra.clients.client import Client

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Google Gemini LLM.

    This service provides a high-level interface for LLM operations.
    For ADK agents, use LlmAgent directly from google.adk.agents.
    """

    def __init__(self) -> None:
        """Initialize the LLM service with Gemini configuration."""
        settings = get_settings()

        if not settings.gemini_api_key:
            raise ValueError("GOOGLE_API_KEY not configured. Please set it in your .env file.")

        self._client = Client(api_key=settings.gemini_api_key).get_client()
        self._thinking_model = settings.thinking_gemini_model
        self._general_model = settings.general_gemini_model
        logger.info(
            f"LLM service initialized with models: "
            f"thinking={self._thinking_model}, general={self._general_model}"
        )

    async def generate_text(
        self,
        content: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_instruction: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text completion using Gemini.

        Args:
            content: The input content for text generation.
            model: Model to use (defaults to general_gemini_model).
            temperature: Controls randomness (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.
            system_instruction: Optional system instruction for the model.
            **kwargs: Additional generation parameters.

        Returns:
            str: Generated text response.

        Raises:
            Exception: If generation fails.
        """
        try:
            model_name = model or self._general_model

            generation_config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                system_instruction=system_instruction,
                **kwargs,
            )

            response = await self._client.aio.models.generate_content(
                model=model_name, contents=content, config=generation_config
            )

            if not response.text:
                logger.warning("Empty response from Gemini API")
                return ""

            result: str = str(response.text)
            logger.debug(f"Generated text with {len(result)} characters using {model_name}")
            return result

        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            raise

    async def generate_with_thinking_model(
        self,
        content: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_instruction: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using the thinking model (gemini-2.5-pro).

        Use this for complex reasoning tasks that require deeper analysis.

        Args:
            content: The input content for text generation.
            temperature: Controls randomness (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.
            system_instruction: Optional system instruction for the model.
            **kwargs: Additional generation parameters.

        Returns:
            str: Generated text response.

        Raises:
            Exception: If generation fails.
        """
        return await self.generate_text(
            content=content,
            model=self._thinking_model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_instruction=system_instruction,
            **kwargs,
        )

    async def generate_streaming(
        self,
        content: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_instruction: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Generate text with streaming response.

        Args:
            content: The input content for text generation.
            model: Model to use (defaults to general_gemini_model).
            temperature: Controls randomness (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.
            system_instruction: Optional system instruction for the model.
            **kwargs: Additional generation parameters.

        Yields:
            str: Generated text chunks.

        Raises:
            Exception: If generation fails.
        """
        try:
            model_name = model or self._general_model

            generation_config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                system_instruction=system_instruction,
                **kwargs,
            )

            response = self._client.models.generate_content_stream(
                model=model_name, contents=content, config=generation_config
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Failed to generate streaming text: {e}")
            raise

    def get_client(self) -> genai.Client:
        """Get the underlying Gemini client.

        Returns:
            genai.Client: Gemini client instance.
        """
        return self._client

    def get_thinking_model(self) -> str:
        """Get the thinking model name.

        Returns:
            str: Thinking model name (gemini-2.5-pro).
        """
        return self._thinking_model

    def get_general_model(self) -> str:
        """Get the general model name.

        Returns:
            str: General model name (gemini-2.5-flash).
        """
        return self._general_model


# Global LLM service instance
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance.

    Returns:
        LLMService: Global LLM service instance.
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
