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


class PromptBuilderAgent:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is missing. Add it to backend/.env")

        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
            max_retries=settings.OPENAI_MAX_RETRIES,
        )

    def build_instructions(
        self,
        conversation_state: ConversationState,
    ) -> str:
        return "\n\n".join(
            [
                PROMPT_BUILDER_SYSTEM_PROMPT.strip(),
                "Current conversation state:",
                conversation_state.model_dump_json(indent=2),
            ]
        )

    async def run(
        self,
        conversation_messages: list[dict[str, str]],
        conversation_state: ConversationState,
        user_id: str,
    ) -> AgentLLMResponse:
        started_at = perf_counter()
        instructions = self.build_instructions(conversation_state)
        response_input = list(conversation_messages)
        validation_error = None

        for attempt in range(settings.AGENT_VALIDATION_RETRIES + 1):
            response = await self.create_response(
                instructions=instructions,
                response_input=response_input,
                user_id=user_id,
            )

            content = response.output_text

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
                        usage=response.usage,
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

    async def create_response(
        self,
        instructions: str,
        response_input: list[dict[str, str]],
        user_id: str,
    ):
        return await self.client.responses.create(
            model=settings.LLM_MODEL,
            instructions=instructions,
            input=response_input,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "prompt_builder_agent_response",
                    "strict": True,
                    "schema": AGENT_LLM_RESPONSE_JSON_SCHEMA,
                },
            },
            store=False,
            safety_identifier=user_id,
            prompt_cache_key=user_id,
        )

    def build_repair_message(self, validation_error: Exception | None) -> dict[str, str]:
        return {
            "role": "user",
            "content": (
                "Your previous JSON response failed backend validation. "
                "Return a corrected JSON response only. If you are returning a "
                "final_prompt, review and fix it first: it must be clear, must not "
                "invent details, must be valid XML with root <prompt>, must not have "
                "critical missing information, and prompt_review must accurately pass "
                f"only when fixed. Validation error: {validation_error}"
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
            "Prompt builder LLM response model=%s action=%s validation_attempt=%s latency_ms=%.2f input_tokens=%s output_tokens=%s total_tokens=%s",
            settings.LLM_MODEL,
            llm_response.action,
            validation_attempt,
            latency_ms,
            getattr(usage, "input_tokens", None),
            getattr(usage, "output_tokens", None),
            getattr(usage, "total_tokens", None),
        )
