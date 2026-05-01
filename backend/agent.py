from openai import AsyncOpenAI
from pydantic import ValidationError

from config import settings
from prompts import PROMPT_BUILDER_SYSTEM_PROMPT
from schemas import AgentLLMResponse


class PromptBuilderAgent:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is missing. Add it to backend/.env")

        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def build_messages(
        self,
        conversation_messages: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": PROMPT_BUILDER_SYSTEM_PROMPT,
            },
            *conversation_messages,
        ]

    async def run(
        self,
        conversation_messages: list[dict[str, str]],
    ) -> AgentLLMResponse:
        messages = self.build_messages(conversation_messages)

        try:
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                temperature=settings.LLM_TEMPERATURE,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "prompt_builder_agent_response",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "enum": ["ask_question", "final_prompt"],
                                },
                                "message": {
                                    "type": "string",
                                },
                                "suggestions": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                    },
                                    "maxItems": 6,
                                },
                                "prompt": {
                                    "type": "string",
                                },
                            },
                            "required": [
                                "action",
                                "message",
                                "suggestions",
                                "prompt",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
            )

            content = response.choices[0].message.content

            if not content:
                raise RuntimeError("The LLM returned an empty response.")

            return AgentLLMResponse.model_validate_json(content)

        except ValidationError as error:
            raise RuntimeError(f"The LLM returned invalid JSON: {error}") from error