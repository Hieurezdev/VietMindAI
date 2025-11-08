"""Adapter for LLM service implementing core port interface."""

import logging

from app.core.ports.services import ILLMService
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class LLMServiceAdapter(ILLMService):
    """Adapter that implements ILLMService using the existing LLMService."""

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._llm_service = get_llm_service()
        logger.info("LLMServiceAdapter initialized")

    async def generate_text(
        self,
        content: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_instruction: str | None = None,
    ) -> str:
        """Generate text completion.

        Args:
            content: Input content.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            system_instruction: Optional system instruction.

        Returns:
            str: Generated text.
        """
        return await self._llm_service.generate_text(
            content=content,
            temperature=temperature,
            max_tokens=max_tokens,
            system_instruction=system_instruction,
        )

    async def generate_with_thinking_model(
        self,
        content: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_instruction: str | None = None,
    ) -> str:
        """Generate text with thinking model for complex reasoning.

        Args:
            content: Input content.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            system_instruction: Optional system instruction.

        Returns:
            str: Generated text.
        """
        return await self._llm_service.generate_with_thinking_model(
            content=content,
            temperature=temperature,
            max_tokens=max_tokens,
            system_instruction=system_instruction,
        )
