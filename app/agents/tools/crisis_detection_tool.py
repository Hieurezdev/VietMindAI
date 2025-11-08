"""Crisis detection tool for ADK agents."""

import logging
from typing import Any

# Note: FunctionDeclaration import may vary by ADK version
# from google.adk.tools import FunctionDeclaration

from app.core.domain.value_objects import ChatContext
from app.infra.adapters import CrisisDetectionService, LLMServiceAdapter

logger = logging.getLogger(__name__)

# Initialize services (will be replaced with proper DI later)
_llm_adapter = LLMServiceAdapter()
_crisis_service = CrisisDetectionService(_llm_adapter)


async def detect_crisis_indicators(
    message: str, context_messages: list[str] | None = None
) -> dict[str, Any]:
    """Detect crisis indicators in a message.

    Args:
        message: Message to analyze for crisis indicators.
        context_messages: Recent conversation messages for context.

    Returns:
        dict: Crisis detection results with indicators and severity.
    """
    try:
        # Build context
        context = ChatContext(
            recent_messages=context_messages or [],
            detected_topics=[],
            crisis_indicators=[],
        )

        # Analyze for crisis
        indicators = await _crisis_service.analyze_message(message, context)

        # Assess severity
        severity = await _crisis_service.assess_severity(indicators)

        result = {
            "is_crisis": indicators.is_crisis,
            "severity": severity,
            "confidence": indicators.confidence_score,
            "indicators": {
                "suicide_keywords": indicators.suicide_keywords,
                "self_harm_mentions": indicators.self_harm_mentions,
                "hopelessness_indicators": indicators.hopelessness_indicators,
                "severe_distress_level": indicators.severe_distress_level,
                "immediate_danger_signals": indicators.immediate_danger_signals,
            },
            "severity_score": indicators.severity_score,
        }

        if indicators.is_crisis:
            logger.warning(
                f"Crisis detected: severity={severity}, confidence={indicators.confidence_score}"
            )

        return result

    except Exception as e:
        logger.error(f"Crisis detection tool failed: {e}")
        return {
            "is_crisis": False,
            "severity": "low",
            "confidence": 0.0,
            "error": str(e),
        }


# ADK Function Declaration (to be configured based on ADK version)
# crisis_detection_tool = FunctionDeclaration(...)
# For now, use the function directly
