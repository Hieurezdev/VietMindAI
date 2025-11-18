"""API endpoints for memory operations."""

import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.memory import (
    ChatRequest,
    ChatResponse,
    ConversationContextResponse,
    VectorMemoryCreate,
    VectorMemoryResponse,
    MemoryContext,
    MemorySearchQuery,
    MemorySearchResult,
    ChatHistoryCreate,
    ChatHistoryResponse,
    UserResponse,
)
from app.infra.db.models import ChatHistory, VectorMemory
from app.infra.db.session import get_session
from app.services.memory_service import get_memory_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Process chat with automatic user state management",
)
async def process_chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """Process a chat message with automatic user and memory management.

    If user_id is None, creates a new user state.
    If user_id is provided, retrieves existing memories.

    Args:
        request: Chat request with content and optional user_id.
        session: Database session.

    Returns:
        ChatResponse: Response with user state and memory context.
    """
    try:
        memory_service = get_memory_service()

        # Get or create user
        is_new_user = request.user_id is None
        user = await memory_service.get_or_create_user(
            session=session,
            user_id=request.user_id,
        )

        # Generate or use provided session_id
        session_id = request.session_id or uuid.uuid4()

        # Get conversation context
        context = await memory_service.get_conversation_context(
            session=session,
            user_id=user.user_id,
            query=request.content,
            session_id=session_id,
        )

        # Add user message to short-term memory
        await memory_service.add_short_term_memory(
            session=session,
            user_id=user.user_id,
            content=request.content,
            role="user",
            session_id=session_id,
        )

        # Check if consolidation is needed (15-20 STM threshold)
        consolidation_result = await memory_service.check_and_consolidate(
            session=session,
            user_id=user.user_id,
            session_id=session_id,
        )

        await session.commit()

        # Build response message
        message = f"Processed message from {'new' if is_new_user else 'existing'} user"
        if consolidation_result and consolidation_result.get("consolidated"):
            stm_deleted = consolidation_result.get("stm_deleted", 0)
            ltm_created = consolidation_result.get("ltm_created", 0)
            message += f". Consolidated {stm_deleted} short-term memories into {ltm_created} long-term insights"

        # Build response
        response = ChatResponse(
            user_id=user.user_id,
            session_id=session_id,
            is_new_user=is_new_user,
            short_term_memories=[
                MemoryContext(**mem) for mem in context["short_term"]
            ],
            long_term_memories=[
                MemoryContext(**mem) for mem in context["long_term"]
            ],
            message=message,
        )

        return response

    except Exception as e:
        logger.error(f"Failed to process chat: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat: {str(e)}",
        )


@router.post(
    "/short-term",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create short-term memory",
)
async def create_short_term_memory(
    memory_data: ChatHistoryCreate,
    session: AsyncSession = Depends(get_session),
) -> ChatHistoryResponse:
    """Create a short-term memory for a user.

    Args:
        memory_data: Short-term memory data.
        session: Database session.

    Returns:
        ChatHistoryResponse: Created memory.
    """
    try:
        memory_service = get_memory_service()

        memory = await memory_service.add_short_term_memory(
            session=session,
            user_id=memory_data.user_id,
            content=memory_data.content,
            role=memory_data.role,
            session_id=memory_data.session_id,
            turn_number=memory_data.turn_number,
            expires_in_hours=memory_data.expires_in_hours,
        )

        await session.commit()
        return ChatHistoryResponse.model_validate(memory)

    except Exception as e:
        logger.error(f"Failed to create short-term memory: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create short-term memory: {str(e)}",
        )


@router.get(
    "/short-term/{user_id}",
    response_model=List[ChatHistoryResponse],
    summary="Get short-term memories for a user",
)
async def get_short_term_memories(
    user_id: uuid.UUID,
    session_id: uuid.UUID | None = None,
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
) -> List[ChatHistoryResponse]:
    """Get short-term memories for a user.

    Args:
        user_id: User ID.
        session_id: Filter by session ID (optional).
        limit: Maximum number of memories.
        session: Database session.

    Returns:
        List[ChatHistoryResponse]: Short-term memories.
    """
    try:
        memory_service = get_memory_service()

        memories = await memory_service.get_short_term_memories(
            session=session,
            user_id=user_id,
            session_id=session_id,
            limit=limit,
        )

        return [ChatHistoryResponse.model_validate(mem) for mem in memories]

    except Exception as e:
        logger.error(f"Failed to get short-term memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get short-term memories: {str(e)}",
        )


@router.post(
    "/long-term",
    response_model=VectorMemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create long-term memory",
)
async def create_long_term_memory(
    memory_data: VectorMemoryCreate,
    session: AsyncSession = Depends(get_session),
) -> VectorMemoryResponse:
    """Create a long-term memory for a user.

    Args:
        memory_data: Long-term memory data.
        session: Database session.

    Returns:
        VectorMemoryResponse: Created memory.
    """
    try:
        memory_service = get_memory_service()

        memory = await memory_service.add_long_term_memory(
            session=session,
            user_id=memory_data.user_id,
            content=memory_data.content,
            memory_type=memory_data.memory_type,
            summary=memory_data.summary,
            importance=memory_data.importance,
        )

        await session.commit()
        return VectorMemoryResponse.model_validate(memory)

    except Exception as e:
        logger.error(f"Failed to create long-term memory: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create long-term memory: {str(e)}",
        )


@router.get(
    "/long-term/{user_id}",
    response_model=List[VectorMemoryResponse],
    summary="Get long-term memories for a user",
)
async def get_long_term_memories(
    user_id: uuid.UUID,
    memory_type: str | None = None,
    min_importance: float = 0.0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> List[VectorMemoryResponse]:
    """Get long-term memories for a user.

    Args:
        user_id: User ID.
        memory_type: Filter by memory type (optional).
        min_importance: Minimum importance score.
        limit: Maximum number of memories.
        session: Database session.

    Returns:
        List[VectorMemoryResponse]: Long-term memories.
    """
    try:
        memory_service = get_memory_service()

        memories = await memory_service.get_long_term_memories(
            session=session,
            user_id=user_id,
            memory_type=memory_type,
            min_importance=min_importance,
            limit=limit,
        )

        return [VectorMemoryResponse.model_validate(mem) for mem in memories]

    except Exception as e:
        logger.error(f"Failed to get long-term memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get long-term memories: {str(e)}",
        )


@router.post(
    "/search/short-term",
    response_model=List[MemorySearchResult],
    summary="Search short-term memories",
)
async def search_short_term_memories(
    search_query: MemorySearchQuery,
    session: AsyncSession = Depends(get_session),
) -> List[MemorySearchResult]:
    """Search short-term memories using semantic similarity.

    Args:
        search_query: Search query parameters.
        session: Database session.

    Returns:
        List[MemorySearchResult]: Search results with similarity scores.
    """
    try:
        memory_service = get_memory_service()

        results = await memory_service.search_short_term_memories(
            session=session,
            user_id=search_query.user_id,
            query=search_query.query,
            limit=search_query.limit,
        )

        return [
            MemorySearchResult(
                memory=MemoryContext(
                    content=mem.content,
                    role=mem.role,
                    turn=mem.turn_number,
                ),
                similarity=sim,
            )
            for mem, sim in results
        ]

    except Exception as e:
        logger.error(f"Failed to search short-term memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search short-term memories: {str(e)}",
        )


@router.post(
    "/search/long-term",
    response_model=List[MemorySearchResult],
    summary="Search long-term memories",
)
async def search_long_term_memories(
    search_query: MemorySearchQuery,
    min_importance: float = 0.0,
    session: AsyncSession = Depends(get_session),
) -> List[MemorySearchResult]:
    """Search long-term memories using semantic similarity.

    Args:
        search_query: Search query parameters.
        min_importance: Minimum importance score.
        session: Database session.

    Returns:
        List[MemorySearchResult]: Search results with similarity scores.
    """
    try:
        memory_service = get_memory_service()

        results = await memory_service.search_long_term_memories(
            session=session,
            user_id=search_query.user_id,
            query=search_query.query,
            min_importance=min_importance,
            limit=search_query.limit,
        )

        return [
            MemorySearchResult(
                memory=MemoryContext(
                    content=mem.content,
                    type=mem.memory_type,
                    importance=mem.importance,
                ),
                similarity=sim,
            )
            for mem, sim in results
        ]

    except Exception as e:
        logger.error(f"Failed to search long-term memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search long-term memories: {str(e)}",
        )


@router.get(
    "/context/{user_id}",
    response_model=ConversationContextResponse,
    summary="Get full conversation context",
)
async def get_conversation_context(
    user_id: uuid.UUID,
    query: str,
    session_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
) -> ConversationContextResponse:
    """Get full conversation context including both memory types.

    Args:
        user_id: User ID.
        query: Query for semantic search of long-term memories.
        session_id: Current session ID (optional).
        session: Database session.

    Returns:
        ConversationContextResponse: Full conversation context.
    """
    try:
        memory_service = get_memory_service()

        context = await memory_service.get_conversation_context(
            session=session,
            user_id=user_id,
            query=query,
            session_id=session_id,
        )

        return ConversationContextResponse(
            user_id=user_id,
            short_term=[MemoryContext(**mem) for mem in context["short_term"]],
            long_term=[MemoryContext(**mem) for mem in context["long_term"]],
        )

    except Exception as e:
        logger.error(f"Failed to get conversation context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation context: {str(e)}",
        )


@router.get(
    "/user/{user_id}",
    response_model=UserResponse,
    summary="Get user information",
)
async def get_user_info(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Get user information and memory counts.

    Args:
        user_id: User ID.
        session: Database session.

    Returns:
        UserResponse: User information.
    """
    try:
        from app.infra.db.models import User

        # Get user
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

        # Count memories
        stm_count_stmt = select(func.count()).select_from(ChatHistory).where(
            ChatHistory.user_id == user_id
        )
        stm_result = await session.execute(stm_count_stmt)
        stm_count = stm_result.scalar() or 0

        ltm_count_stmt = select(func.count()).select_from(VectorMemory).where(
            VectorMemory.user_id == user_id
        )
        ltm_result = await session.execute(ltm_count_stmt)
        ltm_count = ltm_result.scalar() or 0

        return UserResponse(
            user_id=user.user_id,
            name=user.name,
            created_at=user.created_at,
            last_interaction=user.last_interaction,
            short_term_count=stm_count,
            long_term_count=ltm_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}",
        )


@router.post(
    "/cleanup",
    status_code=status.HTTP_200_OK,
    summary="Clean up expired memories",
)
async def cleanup_expired_memories(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Clean up expired short-term memories.

    Args:
        session: Database session.

    Returns:
        dict: Number of memories deleted.
    """
    try:
        memory_service = get_memory_service()

        deleted_count = await memory_service.cleanup_expired_memories(session)
        await session.commit()

        return {"deleted_count": deleted_count, "message": f"Cleaned up {deleted_count} expired memories"}

    except Exception as e:
        logger.error(f"Failed to cleanup expired memories: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup expired memories: {str(e)}",
        )


@router.post(
    "/consolidate/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Manually consolidate short-term memories to long-term",
)
async def consolidate_memories(
    user_id: uuid.UUID,
    session_id: uuid.UUID | None = None,
    force: bool = False,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Manually trigger memory consolidation.

    Converts short-term memories into long-term insights using LLM.
    Automatically triggered at 15 STM (soft threshold) or 20 STM (hard threshold).

    Args:
        user_id: User ID.
        session_id: Session ID to consolidate (optional).
        force: Force consolidation even if below threshold.
        session: Database session.

    Returns:
        dict: Consolidation results.
    """
    try:
        memory_service = get_memory_service()

        result = await memory_service.consolidate_short_term_memories(
            session=session,
            user_id=user_id,
            session_id=session_id,
            force=force,
        )

        await session.commit()
        return result

    except Exception as e:
        logger.error(f"Failed to consolidate memories: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to consolidate memories: {str(e)}",
        )
