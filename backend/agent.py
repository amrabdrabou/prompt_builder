import logging
from time import perf_counter

from openai import AsyncOpenAI
from pydantic import ValidationError

from config import settings
from prompts import PROMPT_BUILDER_SYSTEM_PROMPT
from schemas import (
    AGENT_LLM_RESPONSE_JSON_SCHEMA,
    AgentLLMResponse,
    ConversationState,
)

logger = logging.getLogger(__name__)

_RESPONSE_TEXT_FORMAT = {
    "format": {
        "type": "json_schema",
        "name": "prompt_builder_agent_response",
        "strict": True,
        "schema": AGENT_LLM_RESPONSE_JSON_SCHEMA,
    }
}


class PromptBuilderAgent:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is missing. Add it to backend/.env")

        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
            max_retries=settings.OPENAI_MAX_RETRIES,
        )

    def build_instructions(self, conversation_state: ConversationState) -> str:
        return "\n\n".join([
            PROMPT_BUILDER_SYSTEM_PROMPT.strip(),
            "Current conversation state:",
            conversation_state.model_dump_json(indent=2),
        ])

    def trim_history(
        self,
        conversation_messages: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        total_chars = sum(len(m["content"]) for m in conversation_messages)

        if total_chars <= settings.MAX_HISTORY_CHARS:
            return conversation_messages

        trimmed = list(conversation_messages)
        while len(trimmed) > 1 and sum(len(m["content"]) for m in trimmed) > settings.MAX_HISTORY_CHARS:
            trimmed.pop(0)

        logger.warning(
            "History trimmed before OpenAI call dropped=%d original_chars=%d max_chars=%d",
            len(conversation_messages) - len(trimmed),
            total_chars,
            settings.MAX_HISTORY_CHARS,
        )

        return trimmed

    async def _collect_stream(
        self,
        instructions: str,
        response_input: list[dict[str, str]],
        user_id: str,
    ) -> tuple[str, object]:
        """Call OpenAI with stream=True and return (full_text, usage)."""
        full_text = ""
        usage = None

        stream = await self.client.responses.create(
            model=settings.LLM_MODEL,
            instructions=instructions,
            input=response_input,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
            text=_RESPONSE_TEXT_FORMAT,
            store=False,
            safety_identifier=user_id,
            stream=True,
        )

        async for event in stream:
            if event.type == "response.output_text.delta":
                full_text += event.delta
            elif event.type == "response.completed":
                usage = getattr(getattr(event, "response", None), "usage", None)

        return full_text, usage

    async def run(
        self,
        conversation_messages: list[dict[str, str]],
        conversation_state: ConversationState,
        user_id: str,
    ) -> AgentLLMResponse:
        started_at = perf_counter()
        instructions = self.build_instructions(conversation_state)
        response_input = self.trim_history(list(conversation_messages))
        validation_error = None

        for attempt in range(settings.AGENT_VALIDATION_RETRIES + 1):
            content, usage = await self._collect_stream(
                instructions=instructions,
                response_input=response_input,
                user_id=user_id,
            )

            if not content:
                validation_error = RuntimeError("The LLM returned an empty response.")
            else:
                try:
                    llm_response = AgentLLMResponse.model_validate_json(content)
                except ValidationError as error:
                    validation_error = error
                else:
                    self.log_response_metadata(
                        llm_response=llm_response,
                        usage=usage,
                        latency_ms=(perf_counter() - started_at) * 1000,
                        validation_attempt=attempt + 1,
                    )
                    return llm_response

            if attempt < settings.AGENT_VALIDATION_RETRIES:
                response_input = [
                    *conversation_messages,
                    self.build_repair_message(validation_error),
                ]

        raise RuntimeError(
            f"The LLM returned a response that failed validation: {validation_error}"
        ) from validation_error

    async def stream_run(
        self,
        conversation_messages: list[dict[str, str]],
        conversation_state: ConversationState,
        user_id: str,
    ):
        """Yield word-by-word text chunks for ask_question, then yield the AgentLLMResponse."""
        llm_response = await self.run(
            conversation_messages=conversation_messages,
            conversation_state=conversation_state,
            user_id=user_id,
        )

        if llm_response.action == "ask_question":
            words = llm_response.message.split(" ")
            for i, word in enumerate(words):
                yield word + ("" if i == len(words) - 1 else " ")

        yield llm_response

    def build_repair_message(self, validation_error: Exception | None) -> dict[str, str]:
        if isinstance(validation_error, ValidationError):
            error_summary = "; ".join(
                f"{e['type']} at {'.'.join(str(loc) for loc in e['loc'])}"
                for e in validation_error.errors()
            )
        else:
            error_summary = type(validation_error).__name__

        return {
            "role": "user",
            "content": (
                "Your previous JSON response failed backend validation. "
                "Return a corrected JSON response only. If you are returning a "
                "final_prompt, review and fix it first: it must be clear, must not "
                "invent details, must be valid XML with root <prompt>, must not have "
                "critical missing information, must include non-empty role, goal, "
                "context, instructions, constraints, and output_format tags, must not "
                "include placeholders, and prompt_review must accurately pass with "
                f"quality_score >= 85 only when fixed. Validation error: {error_summary}"
            ),
        }

    def log_response_metadata(
        self,
        llm_response: AgentLLMResponse,
        usage,
        latency_ms: float,
        validation_attempt: int,
    ) -> None:
        logger.info(
            "Prompt builder LLM response model=%s action=%s prompt_type=%s quality_score=%s validation_attempt=%s latency_ms=%.2f input_tokens=%s output_tokens=%s total_tokens=%s",
            settings.LLM_MODEL,
            llm_response.action,
            llm_response.conversation_state.prompt_type,
            llm_response.prompt_review.quality_score,
            validation_attempt,
            latency_ms,
            getattr(usage, "input_tokens", None),
            getattr(usage, "output_tokens", None),
            getattr(usage, "total_tokens", None),
        )
