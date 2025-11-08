"""Value objects for the mental health AI system.

Value objects are immutable objects defined by their attributes.
They have no identity and are interchangeable.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class EmbeddingVector(BaseModel):
    """Value object representing an embedding vector."""

    values: list[float]
    dimension: int = 768  # gemini-embedding-001
    model: str = "gemini-embedding-001"

    def model_post_init(self, __context: object) -> None:
        """Validate embedding dimension after model initialization."""
        if len(self.values) != self.dimension:
            raise ValueError(
                f"Embedding dimension must be {self.dimension}, got {len(self.values)}"
            )

    class Config:
        """Pydantic config."""

        frozen = True


class ChatContext(BaseModel):
    """Value object representing conversation context."""

    recent_messages: list[str] = Field(default_factory=list)
    sentiment: str | None = None  # "positive", "neutral", "negative"
    detected_topics: list[str] = Field(default_factory=list)
    crisis_indicators: list[str] = Field(default_factory=list)
    session_duration_minutes: int = 0

    class Config:
        """Pydantic config."""

        frozen = True


class TherapeuticGoal(BaseModel):
    """Value object representing a therapeutic goal."""

    description: str
    category: str  # e.g., "anxiety", "depression", "stress"
    target_date: datetime | None = None
    measurable_outcome: str | None = None

    class Config:
        """Pydantic config."""

        frozen = True


class CrisisIndicators(BaseModel):
    """Value object for crisis detection indicators."""

    suicide_keywords: bool = False
    self_harm_mentions: bool = False
    hopelessness_indicators: bool = False
    severe_distress_level: bool = False
    immediate_danger_signals: bool = False
    confidence_score: float = Field(ge=0.0, le=1.0)

    @property
    def is_crisis(self) -> bool:
        """Check if any crisis indicator is triggered."""
        return any(
            [
                self.suicide_keywords,
                self.self_harm_mentions,
                self.hopelessness_indicators,
                self.severe_distress_level,
                self.immediate_danger_signals,
            ]
        )

    @property
    def severity_score(self) -> float:
        """Calculate overall severity score (0-1)."""
        indicators = [
            self.suicide_keywords,
            self.self_harm_mentions,
            self.hopelessness_indicators,
            self.severe_distress_level,
            self.immediate_danger_signals,
        ]
        triggered = sum(indicators)
        return (triggered / len(indicators)) * self.confidence_score

    class Config:
        """Pydantic config."""

        frozen = True


class AgentResponse(BaseModel):
    """Value object representing an agent's response."""

    content: str
    agent_name: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    tokens_used: int = 0
    processing_time_ms: int = 0
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        frozen = True


class SearchQuery(BaseModel):
    """Value object for RAG search queries."""

    query_text: str
    embedding: EmbeddingVector | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, str] = Field(default_factory=dict)
    min_relevance_score: float = Field(default=0.7, ge=0.0, le=1.0)

    class Config:
        """Pydantic config."""

        frozen = True


class RetrievedDocument(BaseModel):
    """Value object for retrieved documents from RAG."""

    document_id: str
    content: str
    title: str | None = None
    relevance_score: float = Field(ge=0.0, le=1.0)
    source: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        frozen = True


class MentalHealthAssessment(BaseModel):
    """Value object for mental health assessment results."""

    anxiety_level: int | None = Field(None, ge=0, le=10)
    depression_level: int | None = Field(None, ge=0, le=10)
    stress_level: int | None = Field(None, ge=0, le=10)
    overall_wellbeing: int | None = Field(None, ge=0, le=10)
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    notes: str | None = None

    class Config:
        """Pydantic config."""

        frozen = True


class ThoughtRecord(BaseModel):
    """Value object for CBT thought records."""

    situation: str
    automatic_thought: str
    emotion: str
    emotion_intensity: int = Field(ge=0, le=10)
    evidence_for: list[str] = Field(default_factory=list)
    evidence_against: list[str] = Field(default_factory=list)
    balanced_thought: str | None = None
    emotion_after: int | None = Field(None, ge=0, le=10)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        frozen = True
