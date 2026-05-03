import json
from pathlib import Path
from typing import Any

from schemas import AgentLLMResponse


SCENARIO_PATH = Path(__file__).parent / "fixtures" / "agent_behavior_scenarios.json"


def load_eval_scenarios(path: Path = SCENARIO_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        scenarios = json.load(file)

    if not isinstance(scenarios, list):
        raise ValueError("Eval scenarios must be a JSON list.")

    return scenarios


def _normalize(value: str) -> str:
    return " ".join(value.lower().split())


def _contains_all(text: str, terms: list[str]) -> list[str]:
    normalized_text = _normalize(text)

    return [term for term in terms if _normalize(term) not in normalized_text]


def _contains_any(text: str, terms: list[str]) -> list[str]:
    normalized_text = _normalize(text)

    return [term for term in terms if _normalize(term) in normalized_text]


def evaluate_agent_response(
    scenario: dict[str, Any],
    response: AgentLLMResponse,
) -> list[str]:
    """Return human-readable behavior failures for one eval scenario.

    This helper is intentionally offline and deterministic. It does not call the
    model; it checks whether a captured or mocked agent response satisfies the
    fixture's behavior contract.
    """
    failures: list[str] = []
    expected = scenario["expected"]

    if response.action != expected["action"]:
        failures.append(
            f"Expected action {expected['action']!r}, got {response.action!r}."
        )
        return failures

    expected_prompt_type = expected.get("prompt_type")
    if (
        expected_prompt_type
        and response.conversation_state.prompt_type != expected_prompt_type
    ):
        failures.append(
            "Expected prompt_type "
            f"{expected_prompt_type!r}, got {response.conversation_state.prompt_type!r}."
        )

    expected_ready = expected.get("ready_to_finalize")
    if (
        expected_ready is not None
        and response.conversation_state.ready_to_finalize is not expected_ready
    ):
        failures.append(
            "Expected ready_to_finalize "
            f"{expected_ready!r}, got {response.conversation_state.ready_to_finalize!r}."
        )

    missing_fields = expected.get("missing_fields", [])
    actual_missing_fields = {
        _normalize(field) for field in response.conversation_state.missing_fields
    }
    for field in missing_fields:
        if _normalize(field) not in actual_missing_fields:
            failures.append(f"Expected missing field {field!r}.")

    if response.action == "ask_question":
        # Known simplification: valid multi-clause questions like "What format? (PDF or HTML?)"
        # would fail this check. Acceptable for current fixture evaluation.
        if response.message.count("?") != 1:
            failures.append("ask_question response should ask exactly one question.")

        for term in _contains_all(
            response.message,
            expected.get("required_question_terms", []),
        ):
            failures.append(f"Question is missing expected term {term!r}.")

        for term in _contains_any(
            response.message,
            expected.get("forbidden_question_terms", []),
        ):
            failures.append(f"Question includes forbidden sensitive term {term!r}.")

    if response.action == "final_prompt":
        for term in _contains_all(
            response.prompt,
            expected.get("required_prompt_terms", []),
        ):
            failures.append(f"Final prompt is missing expected term {term!r}.")

        for term in _contains_any(
            response.prompt,
            expected.get("forbidden_prompt_terms", []),
        ):
            failures.append(f"Final prompt includes forbidden/invented term {term!r}.")

    return failures
