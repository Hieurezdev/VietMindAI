"""Crisis detection service implementation using LLM."""

import json
import logging

from app.core.domain.value_objects import ChatContext, CrisisIndicators
from app.core.ports.services import ICrisisDetectionService, ILLMService

logger = logging.getLogger(__name__)


class CrisisDetectionService(ICrisisDetectionService):
    """Crisis detection service using LLM analysis."""

    CRISIS_DETECTION_PROMPT = """Phân tích tin nhắn sau để phát hiện các dấu hiệu khủng hoảng tâm lý.

TIN NHẮN: {message}

BỐI CẢNH TRƯỚC ĐÓ: {context}

Hãy đánh giá các chỉ số sau (true/false):
1. suicide_keywords: Có từ khóa liên quan đến tự tử
2. self_harm_mentions: Có đề cập đến tự làm hại bản thân
3. hopelessness_indicators: Có biểu hiện tuyệt vọng, không thấy hy vọng
4. severe_distress_level: Mức độ đau khổ rất cao
5. immediate_danger_signals: Có dấu hiệu nguy hiểm tức thì

Trả về kết quả dưới dạng JSON với các key trên và confidence_score (0.0-1.0).
Chỉ trả về JSON, không có text khác.

Ví dụ: {{"suicide_keywords": true, "self_harm_mentions": false, "hopelessness_indicators": true, "severe_distress_level": true, "immediate_danger_signals": false, "confidence_score": 0.85}}
"""

    SEVERITY_ASSESSMENT_PROMPT = """Dựa trên các chỉ số khủng hoảng sau, xác định mức độ nghiêm trọng.

CHỈ SỐ: {indicators}

Trả về MỘT trong các giá trị sau: low, medium, high, critical

Quy tắc:
- low: Không có hoặc rất ít dấu hiệu
- medium: Có một vài dấu hiệu nhẹ
- high: Có nhiều dấu hiệu hoặc dấu hiệu nghiêm trọng
- critical: Có immediate_danger_signals=true hoặc suicide_keywords=true với confidence cao

Chỉ trả về một từ: low, medium, high, hoặc critical
"""

    def __init__(self, llm_service: ILLMService) -> None:
        """Initialize crisis detection service.

        Args:
            llm_service: LLM service for analysis.
        """
        self._llm_service = llm_service
        logger.info("CrisisDetectionService initialized")

    async def analyze_message(self, message: str, context: ChatContext) -> CrisisIndicators:
        """Analyze message for crisis indicators.

        Args:
            message: Message to analyze.
            context: Conversation context.

        Returns:
            CrisisIndicators: Detected crisis indicators.
        """
        try:
            # Build context string
            context_str = (
                "\n".join(context.recent_messages[-3:]) if context.recent_messages else "Không có"
            )

            # Generate prompt
            prompt = self.CRISIS_DETECTION_PROMPT.format(message=message, context=context_str)

            # Get LLM analysis
            response = await self._llm_service.generate_text(
                content=prompt,
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=200,
            )

            # Parse JSON response
            try:
                # Clean response (remove markdown code blocks if present)
                cleaned_response = response.strip()
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response.split("```")[1]
                    if cleaned_response.startswith("json"):
                        cleaned_response = cleaned_response[4:]
                cleaned_response = cleaned_response.strip()

                indicators_dict = json.loads(cleaned_response)

                indicators = CrisisIndicators(
                    suicide_keywords=indicators_dict.get("suicide_keywords", False),
                    self_harm_mentions=indicators_dict.get("self_harm_mentions", False),
                    hopelessness_indicators=indicators_dict.get("hopelessness_indicators", False),
                    severe_distress_level=indicators_dict.get("severe_distress_level", False),
                    immediate_danger_signals=indicators_dict.get("immediate_danger_signals", False),
                    confidence_score=float(indicators_dict.get("confidence_score", 0.5)),
                )

                logger.info(
                    f"Crisis analysis completed: is_crisis={indicators.is_crisis}, "
                    f"severity={indicators.severity_score}"
                )

                return indicators

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse crisis detection response: {e}")
                # Return safe default
                return CrisisIndicators(
                    suicide_keywords=False,
                    self_harm_mentions=False,
                    hopelessness_indicators=False,
                    severe_distress_level=False,
                    immediate_danger_signals=False,
                    confidence_score=0.0,
                )

        except Exception as e:
            logger.error(f"Crisis detection failed: {e}")
            # Return safe default
            return CrisisIndicators(
                suicide_keywords=False,
                self_harm_mentions=False,
                hopelessness_indicators=False,
                severe_distress_level=False,
                immediate_danger_signals=False,
                confidence_score=0.0,
            )

    async def assess_severity(self, indicators: CrisisIndicators) -> str:
        """Assess severity level from indicators.

        Args:
            indicators: Crisis indicators.

        Returns:
            str: Severity level (low, medium, high, critical).
        """
        try:
            # Quick rules-based assessment for efficiency
            if indicators.immediate_danger_signals:
                return "critical"

            if indicators.suicide_keywords and indicators.confidence_score > 0.7:
                return "critical"

            if indicators.self_harm_mentions and indicators.severe_distress_level:
                return "high"

            if indicators.severity_score > 0.5:
                return "high" if indicators.severity_score > 0.7 else "medium"

            return "low"

        except Exception as e:
            logger.error(f"Severity assessment failed: {e}")
            return "medium"  # Safe default
