"""Memory service for managing user short-term and long-term memories."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.config import get_settings
from app.infra.db.models import ChatHistory, User, VectorMemory
from app.services.embedding_service import get_embedding_service
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing user memories with automatic state creation.

    Handles both short-term (session-based) and long-term (persistent) memories.
    Automatically creates new user state if user_id is None.
    """

    def __init__(self) -> None:
        """Initialize memory service."""
        self._embedding_service = get_embedding_service()
        self._llm_service = get_llm_service()
        self._settings = get_settings()
        logger.info("Memory service initialized")

    async def get_or_create_user(
        self,
        session: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        name: Optional[str] = None,
    ) -> User:
        """Get existing user or create new one if user_id is None.

        Args:
            session: Database session.
            user_id: User ID (if None, creates new user).
            name: Optional user name.

        Returns:
            User: Existing or newly created user.
        """
        try:
            if user_id is None:
                # Create new user with new state
                user = User(
                    user_id=uuid.uuid4(),
                    name=name,
                )
                session.add(user)
                await session.flush()
                logger.info(f"Created new user: {user.user_id}")
                return user

            # Try to get existing user
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                # Update last interaction
                user.last_interaction = datetime.now(timezone.utc)
                await session.flush()
                logger.debug(f"Retrieved existing user: {user_id}")
                return user

            # User ID provided but doesn't exist - create it
            user = User(
                user_id=user_id,
                name=name,
            )
            session.add(user)
            await session.flush()
            logger.info(f"Created user with provided ID: {user_id}")
            return user

        except Exception as e:
            logger.error(f"Failed to get or create user: {e}")
            raise

    async def add_short_term_memory(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        content: str,
        role: str = "user",
        session_id: Optional[uuid.UUID] = None,
        turn_number: int = 0,
        expires_in_hours: Optional[int] = 24,
    ) -> ChatHistory:
        """Add a short-term memory for a user.

        Args:
            session: Database session.
            user_id: User ID.
            content: Memory content.
            role: Role (user, assistant, system).
            session_id: Session ID (creates new if None).
            turn_number: Turn number in conversation.
            expires_in_hours: Hours until expiry (None for no expiry).

        Returns:
            ChatHistory: Created memory.
        """
        try:
            # Calculate expiry
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

            memory = ChatHistory(
                message_id=uuid.uuid4(),
                user_id=user_id,
                session_id=session_id or uuid.uuid4(),
                content=content,
                role=role,
                turn_number=turn_number,
                expires_at=expires_at,
            )

            session.add(memory)
            await session.flush()
            logger.info(f"Added chat history for user {user_id}")
            return memory

        except Exception as e:
            logger.error(f"Failed to add chat history: {e}")
            raise

    async def get_short_term_memories(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
        limit: int = 10,
    ) -> List[ChatHistory]:
        """Get recent short-term memories for a user.

        Args:
            session: Database session.
            user_id: User ID.
            session_id: Filter by session ID (optional).
            limit: Maximum number of memories to return.

        Returns:
            List[ChatHistory]: Recent memories.
        """
        try:
            stmt = select(ChatHistory).where(ChatHistory.user_id == user_id)

            if session_id:
                stmt = stmt.where(ChatHistory.session_id == session_id)

            # Only return non-expired memories
            stmt = stmt.where(
                (ChatHistory.expires_at.is_(None))
                | (ChatHistory.expires_at > datetime.now(timezone.utc))
            )

            stmt = stmt.order_by(ChatHistory.turn_number.desc()).limit(limit)

            result = await session.execute(stmt)
            memories = list(result.scalars().all())

            logger.debug(f"Retrieved {len(memories)} short-term memories for user {user_id}")
            return memories

        except Exception as e:
            logger.error(f"Failed to get short-term memories: {e}")
            raise

    async def search_short_term_memories(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        limit: int = 5,
    ) -> List[Tuple[ChatHistory, float]]:
        """Search short-term memories (returns recent memories since ChatHistory has no embeddings).

        Args:
            session: Database session.
            user_id: User ID.
            query: Search query (unused for ChatHistory).
            limit: Maximum number of results.

        Returns:
            List of tuples (memory, similarity_score). Score is always 1.0 since no semantic search.
        """
        try:
            # ChatHistory doesn't have embeddings, so just return recent memories
            memories = await self.get_short_term_memories(
                session=session,
                user_id=user_id,
                limit=limit,
            )

            # Return with default similarity score of 1.0
            results: List[Tuple[ChatHistory, float]] = [
                (mem, 1.0) for mem in memories
            ]

            logger.info(f"Found {len(results)} chat history entries")
            return results

        except Exception as e:
            logger.error(f"Failed to search chat history: {e}")
            raise

    async def add_long_term_memory(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        content: str,
        memory_type: str = "general",
        summary: str = "",
        importance: float = 0.5,
    ) -> VectorMemory:
        """Add a long-term memory for a user.

        Args:
            session: Database session.
            user_id: User ID.
            content: Memory content.
            memory_type: Type (preference, fact, context, goal, etc.).
            summary: Brief summary.
            importance: Importance score (0.0 to 1.0).

        Returns:
            VectorMemory: Created memory.
        """
        try:
            # Generate embedding
            embedding = await self._embedding_service.embed_document_async(content)

            memory = VectorMemory(
                memory_id=uuid.uuid4(),
                user_id=user_id,
                content=content,
                memory_type=memory_type,
                summary=summary,
                importance=max(0.0, min(1.0, importance)),  # Clamp to 0-1
                embedding=embedding,
                access_count=0,
            )

            session.add(memory)
            await session.flush()
            logger.info(f"Added long-term memory for user {user_id}")
            return memory

        except Exception as e:
            logger.error(f"Failed to add long-term memory: {e}")
            raise

    async def get_long_term_memories(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        memory_type: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 20,
    ) -> List[VectorMemory]:
        """Get long-term memories for a user.

        Args:
            session: Database session.
            user_id: User ID.
            memory_type: Filter by type (optional).
            min_importance: Minimum importance score.
            limit: Maximum number of memories.

        Returns:
            List[VectorMemory]: Long-term memories.
        """
        try:
            stmt = select(VectorMemory).where(VectorMemory.user_id == user_id)

            if memory_type:
                stmt = stmt.where(VectorMemory.memory_type == memory_type)

            stmt = stmt.where(VectorMemory.importance >= min_importance)
            stmt = stmt.order_by(VectorMemory.importance.desc()).limit(limit)

            result = await session.execute(stmt)
            memories = list(result.scalars().all())

            logger.debug(f"Retrieved {len(memories)} long-term memories for user {user_id}")
            return memories

        except Exception as e:
            logger.error(f"Failed to get long-term memories: {e}")
            raise

    async def search_long_term_memories(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        min_importance: float = 0.0,
        limit: int = 5,
    ) -> List[Tuple[VectorMemory, float]]:
        """Search long-term memories using semantic similarity.

        Args:
            session: Database session.
            user_id: User ID.
            query: Search query.
            min_importance: Minimum importance score.
            limit: Maximum number of results.

        Returns:
            List of tuples (memory, similarity_score).
        """
        try:
            from sqlalchemy import text

            # Generate query embedding
            query_embedding = await self._embedding_service.embed_query_async(query)

            # Similarity search
            similarity_expr = text(
                "1 - (embedding <=> CAST(:query_embedding AS vector))"
            )

            stmt = (
                select(VectorMemory, similarity_expr.label("similarity"))
                .where(VectorMemory.user_id == user_id)
                .where(VectorMemory.importance >= min_importance)
                .order_by(text("similarity DESC"))
                .limit(limit)
                .params(query_embedding=str(query_embedding))
            )

            result = await session.execute(stmt)
            rows = result.all()

            # Update access count and last_accessed
            for row in rows:
                memory = row[0]
                memory.access_count += 1
                memory.last_accessed = datetime.now(timezone.utc)

            await session.flush()

            results: List[Tuple[VectorMemory, float]] = [
                (row[0], float(row[1])) for row in rows
            ]

            logger.info(f"Found {len(results)} similar long-term memories")
            return results

        except Exception as e:
            logger.error(f"Failed to search long-term memories: {e}")
            raise

    async def cleanup_expired_memories(self, session: AsyncSession) -> int:
        """Clean up expired short-term memories.

        Args:
            session: Database session.

        Returns:
            int: Number of memories deleted.
        """
        try:
            stmt = delete(ChatHistory).where(
                ChatHistory.expires_at.is_not(None),
                ChatHistory.expires_at <= datetime.now(timezone.utc),
            )

            result = await session.execute(stmt)
            deleted_count = result.rowcount

            logger.info(f"Cleaned up {deleted_count} expired memories")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired memories: {e}")
            raise

    async def get_conversation_context(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        session_id: Optional[uuid.UUID] = None,
        short_term_limit: int = 5,
        long_term_limit: int = 3,
    ) -> dict:
        """Get full conversation context including both memory types.

        Args:
            session: Database session.
            user_id: User ID.
            query: Current query for semantic search.
            session_id: Current session ID (optional).
            short_term_limit: Max short-term memories.
            long_term_limit: Max long-term memories.

        Returns:
            dict: Context with short-term and long-term memories.
        """
        try:
            # Get recent short-term memories
            recent_memories = await self.get_short_term_memories(
                session=session,
                user_id=user_id,
                session_id=session_id,
                limit=short_term_limit,
            )

            # Search relevant long-term memories
            relevant_ltm = await self.search_long_term_memories(
                session=session,
                user_id=user_id,
                query=query,
                min_importance=0.3,
                limit=long_term_limit,
            )

            context = {
                "user_id": str(user_id),
                "short_term": [
                    {
                        "content": mem.content,
                        "role": mem.role,
                        "turn": mem.turn_number,
                    }
                    for mem in reversed(recent_memories)  # Chronological order
                ],
                "long_term": [
                    {
                        "content": mem.content,
                        "type": mem.memory_type,
                        "importance": mem.importance,
                        "similarity": sim,
                    }
                    for mem, sim in relevant_ltm
                ],
            }

            logger.info(
                f"Built context: {len(context['short_term'])} STM, {len(context['long_term'])} LTM"
            )
            return context

        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            raise

    async def count_short_term_memories(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
    ) -> int:
        """Count short-term memories for a user.

        Args:
            session: Database session.
            user_id: User ID.
            session_id: Filter by session ID (optional).

        Returns:
            int: Number of short-term memories.
        """
        try:
            from sqlalchemy import func

            stmt = select(func.count()).select_from(ChatHistory).where(
                ChatHistory.user_id == user_id
            )

            if session_id:
                stmt = stmt.where(ChatHistory.session_id == session_id)

            # Only count non-expired memories
            stmt = stmt.where(
                (ChatHistory.expires_at.is_(None))
                | (ChatHistory.expires_at > datetime.now(timezone.utc))
            )

            result = await session.execute(stmt)
            count = result.scalar() or 0

            return count

        except Exception as e:
            logger.error(f"Failed to count short-term memories: {e}")
            raise

    async def _summarize_memories_with_llm(
        self, memories: List[ChatHistory]
    ) -> dict:
        """Use LLM to summarize short-term memories and extract insights.

        Args:
            memories: List of short-term memories to summarize.

        Returns:
            dict: Extracted insights with summaries and importance scores.
        """
        try:
            # Format memories for LLM
            conversation_text = "\n\n".join([
                f"[{mem.role.upper()}]: {mem.content}"
                for mem in sorted(memories, key=lambda m: m.turn_number)
            ])

            prompt = f"""Analyze the following conversation and extract important long-term insights about the user:

{conversation_text}

Please extract:
1. User preferences (things they like/dislike)
2. Important facts about the user
3. Goals or aspirations mentioned
4. Triggers or challenges (anxiety, stress causes)
5. Coping strategies that work for them
6. General context worth remembering

For each insight, provide:
- Type: preference|fact|goal|trigger|coping|context
- Content: The actual insight (1-2 sentences)
- Summary: Brief summary (5-10 words)
- Importance: Score from 0.0 to 1.0

Format as JSON array:
[
  {{
    "type": "preference",
    "content": "User prefers morning therapy sessions",
    "summary": "Prefers morning sessions",
    "importance": 0.7
  }}
]

Return ONLY valid JSON array, nothing else."""

            # Get LLM response
            response = await self._llm_service.generate_text_async(prompt)

            # Parse JSON response
            import json
            try:
                # Clean response (remove markdown code blocks if present)
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()

                insights = json.loads(cleaned_response)

                if not isinstance(insights, list):
                    insights = []

                logger.info(f"Extracted {len(insights)} insights from {len(memories)} memories")
                return {"insights": insights, "memory_count": len(memories)}

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.debug(f"LLM response: {response}")
                # Return empty insights on parse error
                return {"insights": [], "memory_count": len(memories)}

        except Exception as e:
            logger.error(f"Failed to summarize memories with LLM: {e}")
            # Return empty insights on error
            return {"insights": [], "memory_count": len(memories)}

    async def consolidate_short_term_memories(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
        force: bool = False,
    ) -> dict:
        """Consolidate short-term memories into long-term memories.

        Automatically triggered when STM count reaches threshold.
        Uses LLM to extract meaningful insights from conversation history.

        Args:
            session: Database session.
            user_id: User ID.
            session_id: Session ID to consolidate (optional, consolidates all if None).
            force: Force consolidation even if below threshold.

        Returns:
            dict: Consolidation results with counts and created LTM.
        """
        try:
            # Count current STM
            stm_count = await self.count_short_term_memories(
                session=session,
                user_id=user_id,
                session_id=session_id,
            )

            # Check if consolidation is needed
            should_consolidate = force or stm_count >= self._settings.stm_consolidation_threshold

            if not should_consolidate:
                logger.debug(
                    f"Skipping consolidation: {stm_count}/{self._settings.stm_consolidation_threshold} STM"
                )
                return {
                    "consolidated": False,
                    "reason": "Below threshold",
                    "stm_count": stm_count,
                    "threshold": self._settings.stm_consolidation_threshold,
                }

            logger.info(
                f"Starting memory consolidation for user {user_id} ({stm_count} STM)"
            )

            # Get all STM for consolidation
            stmt = select(ChatHistory).where(ChatHistory.user_id == user_id)

            if session_id:
                stmt = stmt.where(ChatHistory.session_id == session_id)

            # Only non-expired memories
            stmt = stmt.where(
                (ChatHistory.expires_at.is_(None))
                | (ChatHistory.expires_at > datetime.now(timezone.utc))
            )

            stmt = stmt.order_by(ChatHistory.turn_number.asc())

            result = await session.execute(stmt)
            memories = list(result.scalars().all())

            if not memories:
                return {
                    "consolidated": False,
                    "reason": "No memories to consolidate",
                    "stm_count": 0,
                }

            # Use LLM to extract insights
            summary_result = await self._summarize_memories_with_llm(memories)
            insights = summary_result.get("insights", [])

            # Create long-term memories from insights
            created_ltm = []
            for insight in insights:
                try:
                    ltm = await self.add_long_term_memory(
                        session=session,
                        user_id=user_id,
                        content=insight.get("content", ""),
                        memory_type=insight.get("type", "general"),
                        summary=insight.get("summary", ""),
                        importance=float(insight.get("importance", 0.5)),
                    )
                    created_ltm.append(ltm)
                except Exception as e:
                    logger.error(f"Failed to create LTM from insight: {e}")
                    continue

            # Delete consolidated STM
            delete_stmt = delete(ChatHistory).where(
                ChatHistory.message_id.in_([mem.message_id for mem in memories])
            )
            delete_result = await session.execute(delete_stmt)
            deleted_count = delete_result.rowcount

            logger.info(
                f"Consolidated {deleted_count} STM into {len(created_ltm)} LTM for user {user_id}"
            )

            return {
                "consolidated": True,
                "stm_deleted": deleted_count,
                "ltm_created": len(created_ltm),
                "insights": insights,
                "forced": force,
            }

        except Exception as e:
            logger.error(f"Failed to consolidate memories: {e}")
            raise

    async def check_and_consolidate(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID] = None,
    ) -> Optional[dict]:
        """Check if consolidation is needed and perform it.

        This should be called after adding new short-term memories.

        Args:
            session: Database session.
            user_id: User ID.
            session_id: Session ID (optional).

        Returns:
            dict: Consolidation results if performed, None otherwise.
        """
        try:
            stm_count = await self.count_short_term_memories(
                session=session,
                user_id=user_id,
                session_id=session_id,
            )

            # Check thresholds
            if stm_count >= self._settings.stm_max_threshold:
                logger.warning(
                    f"Max STM threshold reached ({stm_count}/{self._settings.stm_max_threshold}), forcing consolidation"
                )
                return await self.consolidate_short_term_memories(
                    session=session,
                    user_id=user_id,
                    session_id=session_id,
                    force=True,
                )
            elif stm_count >= self._settings.stm_consolidation_threshold:
                logger.info(
                    f"STM threshold reached ({stm_count}/{self._settings.stm_consolidation_threshold}), consolidating"
                )
                return await self.consolidate_short_term_memories(
                    session=session,
                    user_id=user_id,
                    session_id=session_id,
                    force=False,
                )

            return None

        except Exception as e:
            logger.error(f"Failed to check and consolidate: {e}")
            raise


# Global memory service instance
_memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """Get or create the global memory service instance.

    Returns:
        MemoryService: Global memory service instance.
    """
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
