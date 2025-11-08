"""API dependencies for dependency injection."""

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.agents.agent import root_agent
from app.core.models.auth import User
from app.infra.adapters import (
    AgentOrchestrationService,
    CrisisDetectionService,
    EmbeddingServiceAdapter,
    LLMServiceAdapter,
)

logger = logging.getLogger(__name__)
security = HTTPBearer()


# Service dependencies
@lru_cache(maxsize=1)
def get_llm_service_adapter() -> LLMServiceAdapter:
    """Get LLM service adapter singleton."""
    return LLMServiceAdapter()


@lru_cache(maxsize=1)
def get_embedding_service_adapter() -> EmbeddingServiceAdapter:
    """Get embedding service adapter singleton."""
    return EmbeddingServiceAdapter()


@lru_cache(maxsize=1)
def get_crisis_detection_service() -> CrisisDetectionService:
    """Get crisis detection service singleton."""
    llm_adapter = get_llm_service_adapter()
    return CrisisDetectionService(llm_adapter)


@lru_cache(maxsize=1)
def get_agent_orchestration_service() -> AgentOrchestrationService:
    """Get agent orchestration service singleton."""
    return AgentOrchestrationService(root_agent)


# Auth dependencies
async def get_current_user(token: Annotated[str, Depends(security)]) -> User:
    """Get current authenticated user."""
    # TODO: Implement actual authentication logic
    # For now, return a mock user
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    return User(id="mock-user-id", email="user@example.com", name="Mock User")
