from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


PROMPT_TYPE_VALUES = (
    "writing",
    "coding",
    "marketing",
    "analysis",
    "research",
    "planning",
    "image_generation",
    "automation",
    "other",
)
MESSAGE_ROLE_VALUES = ("user", "assistant")
RATE_LIMIT_ACTION_VALUES = ("chat",)

PROMPT_TYPE_CHECK_SQL = (
    "prompt_type IN ("
    + ", ".join(f"'{prompt_type}'" for prompt_type in PROMPT_TYPE_VALUES)
    + ")"
)
MESSAGE_ROLE_CHECK_SQL = (
    "role IN ("
    + ", ".join(f"'{role}'" for role in MESSAGE_ROLE_VALUES)
    + ")"
)
RATE_LIMIT_ACTION_CHECK_SQL = (
    "action IN ("
    + ", ".join(f"'{action}'" for action in RATE_LIMIT_ACTION_VALUES)
    + ")"
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    google_sub: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    picture_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(
            PROMPT_TYPE_CHECK_SQL,
            name="ck_conversations_prompt_type",
        ),
    )

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    goal: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    audience: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    constraints: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    output_format: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    prompt_type: Mapped[str] = mapped_column(
        String(50),
        default="other",
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(120),
        default="",
        nullable=False,
    )

    confidence: Mapped[dict[str, int]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    missing_fields: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    ready_to_finalize: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    user: Mapped[User] = relationship(
        back_populates="conversations",
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    final_prompts: Mapped[list["FinalPrompt"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class FinalPrompt(Base):
    __tablename__ = "final_prompts"
    __table_args__ = (
        CheckConstraint(
            PROMPT_TYPE_CHECK_SQL,
            name="ck_final_prompts_prompt_type",
        ),
        CheckConstraint(
            "quality_score >= 0 AND quality_score <= 100",
            name="ck_final_prompts_quality_score_range",
        ),
    )

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    prompt_type: Mapped[str] = mapped_column(
        String(50),
        default="other",
        nullable=False,
    )

    quality_score: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    review: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    conversation: Mapped[Conversation] = relationship(
        back_populates="final_prompts",
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            MESSAGE_ROLE_CHECK_SQL,
            name="ck_messages_role",
        ),
    )

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    conversation: Mapped[Conversation] = relationship(
        back_populates="messages",
    )


class RateLimitEvent(Base):
    __tablename__ = "rate_limit_events"
    __table_args__ = (
        CheckConstraint(
            RATE_LIMIT_ACTION_CHECK_SQL,
            name="ck_rate_limit_events_action",
        ),
        Index(
            "ix_rate_limit_events_user_action_created_at",
            "user_id",
            "action",
            "created_at",
        ),
    )

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
