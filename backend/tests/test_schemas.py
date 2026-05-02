import unittest

from pydantic import ValidationError

from schemas import (
    AGENT_LLM_RESPONSE_JSON_SCHEMA,
    AgentLLMResponse,
    ConversationState,
    MAX_AGENT_QUESTION_LENGTH,
    MAX_FINAL_PROMPT_LENGTH,
    MAX_SUGGESTION_LENGTH,
    PromptReview,
)


class AgentLLMResponseTests(unittest.TestCase):
    def test_accepts_valid_question_response(self):
        response = AgentLLMResponse(
            action="ask_question",
            message="Who is the audience?",
            suggestions=["Developers", "Students", "Managers"],
            prompt="",
            conversation_state=ConversationState(
                goal="Create a prompt",
                missing_fields=["Audience"],
                ready_to_finalize=False,
            ),
            prompt_review=PromptReview(),
        )

        self.assertEqual(response.action, "ask_question")
        self.assertEqual(response.suggestions, ["Developers", "Students", "Managers"])

    def test_rejects_final_prompt_without_ready_state(self):
        with self.assertRaises(ValidationError):
            AgentLLMResponse(
                action="final_prompt",
                message="",
                suggestions=[],
                prompt="<prompt>Do the task.</prompt>",
                conversation_state=ConversationState(ready_to_finalize=False),
                prompt_review=PromptReview(),
            )

    def test_deduplicates_and_limits_list_fields(self):
        state = ConversationState(
            constraints=[" concise ", "concise", "", "Use bullets"],
            missing_fields=[str(index) for index in range(20)],
        )

        self.assertEqual(state.constraints, ["concise", "Use bullets"])
        self.assertEqual(len(state.missing_fields), 12)

    def test_rejects_oversized_conversation_state_fields(self):
        with self.assertRaises(ValidationError):
            ConversationState(title="x" * 121)

    def test_accepts_reviewed_valid_final_prompt(self):
        response = AgentLLMResponse(
            action="final_prompt",
            message="",
            suggestions=[],
            prompt=(
                "<prompt>"
                "<role>Act as a concise writing assistant.</role>"
                "<goal>Create a summary.</goal>"
                "<context>User needs a short summary.</context>"
                "<instructions>Write clearly.</instructions>"
                "<constraints>Do not invent details.</constraints>"
                "<output_format>Return bullets.</output_format>"
                "</prompt>"
            ),
            conversation_state=ConversationState(
                goal="Create a summary prompt",
                ready_to_finalize=True,
            ),
            prompt_review=PromptReview(
                is_clear=True,
                uses_only_known_details=True,
                is_xml_valid=True,
                no_missing_critical_info=True,
                ready_to_return=True,
                quality_score=92,
            ),
        )

        self.assertEqual(response.action, "final_prompt")

    def test_rejects_final_prompt_with_invalid_xml(self):
        with self.assertRaises(ValidationError):
            AgentLLMResponse(
                action="final_prompt",
                message="",
                suggestions=[],
                prompt="<prompt><role>Broken</prompt>",
                conversation_state=ConversationState(ready_to_finalize=True),
                prompt_review=PromptReview(
                    is_clear=True,
                    uses_only_known_details=True,
                    is_xml_valid=True,
                    no_missing_critical_info=True,
                    ready_to_return=True,
                    quality_score=92,
                ),
            )

    def test_rejects_final_prompt_with_failed_review(self):
        with self.assertRaises(ValidationError):
            AgentLLMResponse(
                action="final_prompt",
                message="",
                suggestions=[],
                prompt="<prompt><role>Act as an assistant.</role></prompt>",
                conversation_state=ConversationState(ready_to_finalize=True),
                prompt_review=PromptReview(
                    is_clear=True,
                    uses_only_known_details=False,
                    is_xml_valid=True,
                    no_missing_critical_info=True,
                    ready_to_return=True,
                    quality_score=92,
                ),
            )

    def test_rejects_final_prompt_with_low_quality_score(self):
        with self.assertRaises(ValidationError):
            AgentLLMResponse(
                action="final_prompt",
                message="",
                suggestions=[],
                prompt=(
                    "<prompt>"
                    "<role>Act as an assistant.</role>"
                    "<goal>Create a prompt.</goal>"
                    "<context>User provided a rough idea.</context>"
                    "<instructions>Help with the task.</instructions>"
                    "<constraints>Do not invent details.</constraints>"
                    "<output_format>Return a clear answer.</output_format>"
                    "</prompt>"
                ),
                conversation_state=ConversationState(ready_to_finalize=True),
                prompt_review=PromptReview(
                    is_clear=True,
                    uses_only_known_details=True,
                    is_xml_valid=True,
                    no_missing_critical_info=True,
                    ready_to_return=True,
                    quality_score=84,
                ),
                )

    def test_rejects_oversized_agent_question(self):
        with self.assertRaises(ValidationError):
            AgentLLMResponse(
                action="ask_question",
                message="x" * (MAX_AGENT_QUESTION_LENGTH + 1),
                suggestions=[],
                prompt="",
                conversation_state=ConversationState(),
                prompt_review=PromptReview(),
            )

    def test_rejects_oversized_suggestion(self):
        with self.assertRaises(ValidationError):
            AgentLLMResponse(
                action="ask_question",
                message="Who is the audience?",
                suggestions=["x" * (MAX_SUGGESTION_LENGTH + 1)],
                prompt="",
                conversation_state=ConversationState(),
                prompt_review=PromptReview(),
            )

    def test_rejects_oversized_final_prompt(self):
        with self.assertRaises(ValidationError):
            AgentLLMResponse(
                action="final_prompt",
                message="",
                suggestions=[],
                prompt="x" * (MAX_FINAL_PROMPT_LENGTH + 1),
                conversation_state=ConversationState(ready_to_finalize=True),
                prompt_review=PromptReview(
                    is_clear=True,
                    uses_only_known_details=True,
                    is_xml_valid=True,
                    no_missing_critical_info=True,
                    ready_to_return=True,
                    quality_score=92,
                ),
            )

    def test_rejects_final_prompt_missing_required_xml_tag(self):
        with self.assertRaises(ValidationError):
            AgentLLMResponse(
                action="final_prompt",
                message="",
                suggestions=[],
                prompt=(
                    "<prompt>"
                    "<role>Act as an assistant.</role>"
                    "<goal>Create a prompt.</goal>"
                    "<context>User provided a rough idea.</context>"
                    "<instructions>Help with the task.</instructions>"
                    "<constraints>Do not invent details.</constraints>"
                    "</prompt>"
                ),
                conversation_state=ConversationState(ready_to_finalize=True),
                prompt_review=PromptReview(
                    is_clear=True,
                    uses_only_known_details=True,
                    is_xml_valid=True,
                    no_missing_critical_info=True,
                    ready_to_return=True,
                    quality_score=92,
                ),
            )

    def test_rejects_final_prompt_with_unresolved_placeholder(self):
        with self.assertRaises(ValidationError):
            AgentLLMResponse(
                action="final_prompt",
                message="",
                suggestions=[],
                prompt=(
                    "<prompt>"
                    "<role>Act as an assistant.</role>"
                    "<goal>Create a prompt for [insert task].</goal>"
                    "<context>User provided a rough idea.</context>"
                    "<instructions>Help with the task.</instructions>"
                    "<constraints>Do not invent details.</constraints>"
                    "<output_format>Return a clear answer.</output_format>"
                    "</prompt>"
                ),
                conversation_state=ConversationState(ready_to_finalize=True),
                prompt_review=PromptReview(
                    is_clear=True,
                    uses_only_known_details=True,
                    is_xml_valid=True,
                    no_missing_critical_info=True,
                    ready_to_return=True,
                    quality_score=92,
                ),
            )

    def test_clamps_confidence_scores(self):
        state = ConversationState(
            confidence={
                "goal": 120,
                "audience": -5,
                "constraints": 55,
                "output_format": 88,
            }
        )

        self.assertEqual(state.confidence.goal, 100)
        self.assertEqual(state.confidence.audience, 0)

    def test_openai_schema_preserves_conversation_title_field(self):
        properties = AGENT_LLM_RESPONSE_JSON_SCHEMA["$defs"]["ConversationState"][
            "properties"
        ]

        self.assertIn("title", properties)
        self.assertFalse("default" in str(AGENT_LLM_RESPONSE_JSON_SCHEMA))


if __name__ == "__main__":
    unittest.main()
