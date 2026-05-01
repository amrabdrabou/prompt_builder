from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
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


class AskQuestionResponse(BaseModel):
    action: Literal["ask_question"]
    conversation_id: str
    message: str = Field(..., min_length=1)
    suggestions: list[str] = Field(default_factory=list)


class FinalPromptResponse(BaseModel):
    action: Literal["final_prompt"]
    conversation_id: str
    prompt: str = Field(..., min_length=1)



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

    @field_validator("suggestions")
    @classmethod
    def limit_suggestions(cls, value: list[str]) -> list[str]:
        return value[:6]


AgentResponse = AskQuestionResponse | FinalPromptResponse