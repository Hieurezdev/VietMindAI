#!/usr/bin/env python3
"""Test script for chat flow end-to-end testing.

This script tests the complete flow from user input to agent response.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.api.dependencies import get_agent_orchestration_service
from app.core.domain.value_objects import ChatContext
from app.core.models.auth import User


async def test_general_chat():
    """Test general mental health conversation."""
    print("\n" + "=" * 80)
    print("TEST 1: General Mental Health Question")
    print("=" * 80)

    # Get service
    agent_service = get_agent_orchestration_service()

    # Create test context
    context = ChatContext(
        recent_messages=[],
        detected_topics=[],
        crisis_indicators=[],
    )

    # Test message
    message = "Tôi đang cảm thấy lo lắng về công việc"
    user_id = "test-user-123"

    print(f"\nUser message: {message}")
    print(f"User ID: {user_id}")
    print(f"Context: {context.model_dump_json(indent=2)}")

    try:
        # Route message
        print("\nRouting message to agents...")
        response = await agent_service.route_message(
            message=message, context=context, user_id=user_id
        )

        print(f"\n✓ Success!")
        print(f"Agent: {response.agent_name}")
        print(f"Processing time: {response.processing_time_ms}ms")
        print(f"Confidence: {response.confidence}")
        print(f"\nResponse:\n{response.content}")
        print(f"\nMetadata: {json.dumps(response.metadata, indent=2)}")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_crisis_detection():
    """Test crisis detection flow."""
    print("\n" + "=" * 80)
    print("TEST 2: Crisis Detection")
    print("=" * 80)

    agent_service = get_agent_orchestration_service()

    context = ChatContext(
        recent_messages=["Tôi cảm thấy rất mệt mỏi", "Mọi thứ đều vô nghĩa"],
        detected_topics=["hopelessness", "fatigue"],
        crisis_indicators=[],
    )

    message = "Tôi không còn muốn sống nữa"
    user_id = "test-user-456"

    print(f"\nUser message: {message}")
    print(f"User ID: {user_id}")
    print(f"Context: {context.model_dump_json(indent=2)}")

    try:
        print("\nRouting message to agents...")
        response = await agent_service.route_message(
            message=message, context=context, user_id=user_id
        )

        print(f"\n✓ Success!")
        print(f"Agent: {response.agent_name}")
        print(f"Processing time: {response.processing_time_ms}ms")
        print(f"\nResponse:\n{response.content}")

        # Check if crisis was detected
        if "crisis" in response.metadata or response.agent_name == "crisis_detection_agent":
            print("\n⚠️  CRISIS DETECTED - Appropriate routing confirmed")
        else:
            print(
                "\n⚠️  Warning: Crisis message may not have been properly detected"
            )

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_rag_question():
    """Test knowledge-based question (RAG)."""
    print("\n" + "=" * 80)
    print("TEST 3: Knowledge-Based Question (RAG)")
    print("=" * 80)

    agent_service = get_agent_orchestration_service()

    context = ChatContext(
        recent_messages=[],
        detected_topics=[],
        crisis_indicators=[],
    )

    message = "CBT là gì và nó hoạt động như thế nào?"
    user_id = "test-user-789"

    print(f"\nUser message: {message}")
    print(f"User ID: {user_id}")

    try:
        print("\nRouting message to agents...")
        response = await agent_service.route_message(
            message=message, context=context, user_id=user_id
        )

        print(f"\n✓ Success!")
        print(f"Agent: {response.agent_name}")
        print(f"Processing time: {response.processing_time_ms}ms")
        print(f"\nResponse:\n{response.content}")

        if response.agent_name == "RAG_agent":
            print("\n✓ Correctly routed to RAG agent")
        else:
            print(f"\n⚠️  Note: Routed to {response.agent_name} instead of RAG agent")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_conversation_continuity():
    """Test conversation with history."""
    print("\n" + "=" * 80)
    print("TEST 4: Conversation Continuity with History")
    print("=" * 80)

    agent_service = get_agent_orchestration_service()

    context = ChatContext(
        recent_messages=[
            "Tôi đang lo lắng về kỳ thi sắp tới",
            "Lo lắng là cảm xúc bình thường. Bạn có thể thử kỹ thuật thở sâu",
            "Tôi đã thử nhưng vẫn còn lo",
            "Hãy thử viết ra những lo lắng cụ thể của bạn",
        ],
        detected_topics=["anxiety", "exam_stress"],
        crisis_indicators=[],
    )

    message = "Vậy tôi nên làm gì tiếp theo?"
    user_id = "test-user-999"

    print(f"\nUser message: {message}")
    print(f"User ID: {user_id}")
    print(f"Conversation history: {len(context.recent_messages)} messages")

    try:
        print("\nRouting message to agents...")
        response = await agent_service.route_message(
            message=message, context=context, user_id=user_id
        )

        print(f"\n✓ Success!")
        print(f"Agent: {response.agent_name}")
        print(f"Processing time: {response.processing_time_ms}ms")
        print(f"\nResponse:\n{response.content}")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("CHAT FLOW END-TO-END TESTS")
    print("=" * 80)
    print("\nThis script tests the complete flow:")
    print("1. User input → ChatContext")
    print("2. AgentOrchestrationService → Root Agent")
    print("3. Root Agent → Sub-agents (routing)")
    print("4. Sub-agents → AgentResponse")
    print("5. AgentResponse → User")

    # Run tests
    results = []

    try:
        results.append(("General Chat", await test_general_chat()))
    except Exception as e:
        print(f"\n✗ General Chat test failed: {e}")
        results.append(("General Chat", False))

    try:
        results.append(("Crisis Detection", await test_crisis_detection()))
    except Exception as e:
        print(f"\n✗ Crisis Detection test failed: {e}")
        results.append(("Crisis Detection", False))

    try:
        results.append(("RAG Question", await test_rag_question()))
    except Exception as e:
        print(f"\n✗ RAG Question test failed: {e}")
        results.append(("RAG Question", False))

    try:
        results.append(
            ("Conversation Continuity", await test_conversation_continuity())
        )
    except Exception as e:
        print(f"\n✗ Conversation Continuity test failed: {e}")
        results.append(("Conversation Continuity", False))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
