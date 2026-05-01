import unittest

from pydantic import ValidationError

from schemas import AgentLLMResponse, ConversationState, PromptReview


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
                ),
            )


if __name__ == "__main__":
    unittest.main()
