import unittest

from evals.agent_behavior import evaluate_agent_response, load_eval_scenarios
from schemas import AgentLLMResponse, ConversationState, PromptReview


REQUIRED_CATEGORIES = {
    "vague_request",
    "clear_request",
    "sensitive_request",
    "no_invented_facts",
    "revision_request",
}


def valid_final_prompt(*terms: str) -> str:
    term_text = " ".join(terms)

    return (
        "<prompt>"
        "<role>Act as a careful prompt-writing assistant.</role>"
        f"<goal>Create a prompt covering {term_text}.</goal>"
        f"<context>The known user details are: {term_text}.</context>"
        "<instructions>Use only known details and write a clear reusable prompt.</instructions>"
        "<constraints>Do not invent facts or ask for unnecessary personal data.</constraints>"
        "<output_format>Return the requested structure.</output_format>"
        "</prompt>"
    )


class EvalFixtureTests(unittest.TestCase):
    def test_fixture_set_has_expected_size_unique_ids_and_category_coverage(self):
        scenarios = load_eval_scenarios()

        self.assertGreaterEqual(len(scenarios), 20)
        self.assertLessEqual(len(scenarios), 50)
        self.assertEqual(len({scenario["id"] for scenario in scenarios}), len(scenarios))
        self.assertEqual(
            REQUIRED_CATEGORIES,
            {scenario["category"] for scenario in scenarios},
        )

    def test_each_scenario_has_valid_shape(self):
        for scenario in load_eval_scenarios():
            with self.subTest(scenario=scenario["id"]):
                self.assertIsInstance(scenario["description"], str)
                self.assertTrue(scenario["description"].strip())
                self.assertTrue(scenario["messages"])
                self.assertIn("expected", scenario)

                for message in scenario["messages"]:
                    self.assertIn(message["role"], {"user", "assistant"})
                    self.assertTrue(message["content"].strip())

                expected = scenario["expected"]
                self.assertIn(expected["action"], {"ask_question", "final_prompt"})
                self.assertIn(
                    expected["prompt_type"],
                    {
                        "writing",
                        "coding",
                        "marketing",
                        "analysis",
                        "research",
                        "planning",
                        "image_generation",
                        "automation",
                        "other",
                    },
                )
                self.assertIsInstance(expected["ready_to_finalize"], bool)

                if expected["action"] == "ask_question":
                    self.assertFalse(expected["ready_to_finalize"])
                    self.assertTrue(expected.get("missing_fields"))
                    self.assertTrue(expected.get("required_question_terms"))

                if expected["action"] == "final_prompt":
                    self.assertTrue(expected["ready_to_finalize"])
                    self.assertTrue(expected.get("required_prompt_terms"))
                    self.assertTrue(expected.get("forbidden_prompt_terms"))

    def test_evaluator_accepts_matching_question_response(self):
        scenario = next(
            scenario
            for scenario in load_eval_scenarios()
            if scenario["id"] == "vague-writing-001"
        )
        response = AgentLLMResponse(
            action="ask_question",
            message="What specific writing outcome should the prompt help create?",
            suggestions=["Email", "Article", "Summary"],
            prompt="",
            conversation_state=ConversationState(
                prompt_type="writing",
                missing_fields=["Goal"],
                ready_to_finalize=False,
            ),
            prompt_review=PromptReview(),
        )

        self.assertEqual(evaluate_agent_response(scenario, response), [])

    def test_evaluator_rejects_sensitive_question_terms(self):
        scenario = next(
            scenario
            for scenario in load_eval_scenarios()
            if scenario["id"] == "sensitive-financial-012"
        )
        response = AgentLLMResponse(
            action="ask_question",
            message="What is your goal, account number, and routing number?",
            suggestions=[],
            prompt="",
            conversation_state=ConversationState(
                prompt_type="planning",
                missing_fields=["Financial goal"],
                ready_to_finalize=False,
            ),
            prompt_review=PromptReview(),
        )

        failures = evaluate_agent_response(scenario, response)

        self.assertIn("forbidden sensitive term", " ".join(failures))

    def test_evaluator_accepts_matching_final_prompt_response(self):
        scenario = next(
            scenario
            for scenario in load_eval_scenarios()
            if scenario["id"] == "clear-coding-007"
        )
        response = AgentLLMResponse(
            action="final_prompt",
            message="",
            suggestions=[],
            prompt=valid_final_prompt(
                "Python CLI",
                "CSV",
                "customer_id",
                "JSON",
                "pytest",
                "junior backend developer",
            ),
            conversation_state=ConversationState(
                prompt_type="coding",
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

        self.assertEqual(evaluate_agent_response(scenario, response), [])

    def test_evaluator_rejects_invented_final_prompt_terms(self):
        scenario = next(
            scenario
            for scenario in load_eval_scenarios()
            if scenario["id"] == "no-invention-017"
        )
        response = AgentLLMResponse(
            action="final_prompt",
            message="",
            suggestions=[],
            prompt=valid_final_prompt(
                "SQL query",
                "correctness",
                "performance",
                "readability",
                "severity",
                "suggested rewrites",
                "Django",
            ),
            conversation_state=ConversationState(
                prompt_type="coding",
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

        failures = evaluate_agent_response(scenario, response)

        self.assertIn("forbidden/invented term", " ".join(failures))


if __name__ == "__main__":
    unittest.main()
