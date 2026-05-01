from copy import deepcopy
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime

class ChatRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    user_message: str = Field(..., min_length=1, max_length=4000)

    @field_validator("user_message")
    @classmethod
    def clean_user_message(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("User message cannot be empty.")

        return cleaned


class ConversationState(BaseModel):
    goal: str = ""
    audience: str = ""
    constraints: list[str] = Field(default_factory=list)
    output_format: str = ""
    missing_fields: list[str] = Field(default_factory=list)
    ready_to_finalize: bool = False

    @field_validator("goal", "audience", "output_format")
    @classmethod
    def clean_text_field(cls, value: str) -> str:
        return value.strip()

    @field_validator("constraints", "missing_fields")
    @classmethod
    def clean_list_field(cls, value: list[str]) -> list[str]:
        cleaned_values = []

        for item in value:
            cleaned = item.strip()

            if cleaned and cleaned not in cleaned_values:
                cleaned_values.append(cleaned)

        return cleaned_values[:12]


class PromptReview(BaseModel):
    is_clear: bool = False
    uses_only_known_details: bool = False
    is_xml_valid: bool = False
    no_missing_critical_info: bool = False
    ready_to_return: bool = False
    missing_or_unclear_items: list[str] = Field(default_factory=list)
    fixes_applied: list[str] = Field(default_factory=list)

    @field_validator("missing_or_unclear_items", "fixes_applied")
    @classmethod
    def clean_review_list(cls, value: list[str]) -> list[str]:
        cleaned_values = []

        for item in value:
            cleaned = item.strip()

            if cleaned and cleaned not in cleaned_values:
                cleaned_values.append(cleaned)

        return cleaned_values[:8]


class AskQuestionResponse(BaseModel):
    action: Literal["ask_question"]
    conversation_id: str
    message: str = Field(..., min_length=1)
    suggestions: list[str] = Field(default_factory=list)
    conversation_state: ConversationState


class FinalPromptResponse(BaseModel):
    action: Literal["final_prompt"]
    conversation_id: str
    prompt: str = Field(..., min_length=1)
    conversation_state: ConversationState
    prompt_review: PromptReview



class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None = None
    picture_url: str | None = None
    created_at: datetime

class AgentLLMResponse(BaseModel):
    action: Literal["ask_question", "final_prompt"]
    message: str = ""
    suggestions: list[str] = Field(default_factory=list)
    prompt: str = ""
    conversation_state: ConversationState
    prompt_review: PromptReview

    @field_validator("suggestions")
    @classmethod
    def limit_suggestions(cls, value: list[str]) -> list[str]:
        cleaned_values = []

        for item in value:
            cleaned = item.strip()

            if cleaned and cleaned not in cleaned_values:
                cleaned_values.append(cleaned)

        return cleaned_values[:6]

    @model_validator(mode="after")
    def validate_action_payload(self):
        if self.action == "ask_question":
            if not self.message.strip():
                raise ValueError("ask_question responses must include a message.")

            if self.prompt.strip():
                raise ValueError("ask_question responses must not include a final prompt.")

        if self.action == "final_prompt":
            if not self.prompt.strip():
                raise ValueError("final_prompt responses must include a prompt.")

            if self.message.strip():
                raise ValueError("final_prompt responses must not include a question message.")

            if self.suggestions:
                raise ValueError("final_prompt responses must not include suggestions.")

            if not self.conversation_state.ready_to_finalize:
                raise ValueError("final_prompt responses must mark the state ready to finalize.")

            self.validate_final_prompt_review()
            self.validate_final_prompt_xml()

        return self

    def validate_final_prompt_review(self) -> None:
        if not self.prompt_review.is_clear:
            raise ValueError("final_prompt review must confirm the prompt is clear.")

        if not self.prompt_review.uses_only_known_details:
            raise ValueError("final_prompt review must confirm no details were invented.")

        if not self.prompt_review.is_xml_valid:
            raise ValueError("final_prompt review must confirm the XML is valid.")

        if not self.prompt_review.no_missing_critical_info:
            raise ValueError("final_prompt review must confirm no critical info is missing.")

        if not self.prompt_review.ready_to_return:
            raise ValueError("final_prompt review must mark the prompt ready to return.")

        if self.prompt_review.missing_or_unclear_items:
            raise ValueError("final_prompt review must not include unresolved missing items.")

    def validate_final_prompt_xml(self) -> None:
        try:
            root = ElementTree.fromstring(self.prompt)
        except ParseError as error:
            raise ValueError(f"final_prompt must be valid XML: {error}") from error

        if root.tag != "prompt":
            raise ValueError("final_prompt XML root element must be <prompt>.")


AgentResponse = AskQuestionResponse | FinalPromptResponse


def _strip_schema_metadata(schema: dict[str, Any]) -> dict[str, Any]:
    cleaned_schema = deepcopy(schema)

    def clean(value: Any) -> None:
        if isinstance(value, dict):
            value.pop("default", None)
            value.pop("title", None)

            if value.get("type") == "object":
                properties = value.get("properties", {})
                value["additionalProperties"] = False
                value["required"] = list(properties.keys())

            for child_value in value.values():
                clean(child_value)

        if isinstance(value, list):
            for item in value:
                clean(item)

    clean(cleaned_schema)

    return cleaned_schema


AGENT_LLM_RESPONSE_JSON_SCHEMA = _strip_schema_metadata(
    AgentLLMResponse.model_json_schema()
)
