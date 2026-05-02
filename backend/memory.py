from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Conversation,
    FinalPrompt,
    MESSAGE_ROLE_VALUES,
    RateLimitEvent,
    Message,
    User,
)
from schemas import ConversationState, PromptReview


@dataclass(frozen=True)
class RateLimitPolicy:
    max_requests: int
    window_seconds: int


class RateLimitExceeded(Exception):
    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Rate limit exceeded.")


async def get_user_by_google_sub(
    db: AsyncSession,
    google_sub: str,
) -> User | None:
    result = await db.execute(
        select(User).where(User.google_sub == google_sub)
    )

    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email)
    )

    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    google_sub: str,
    email: str,
    name: str | None = None,
    picture_url: str | None = None,
) -> User:
    user = User(
        google_sub=google_sub,
        email=email,
        name=name,
        picture_url=picture_url,
    )

    db.add(user)
    await db.flush()
    await db.refresh(user)

    return user


async def get_or_create_google_user(
    db: AsyncSession,
    google_sub: str,
    email: str,
    name: str | None = None,
    picture_url: str | None = None,
) -> User:
    user = await get_user_by_google_sub(db, google_sub)

    if user:
        return user

    user = await create_user(
        db=db,
        google_sub=google_sub,
        email=email,
        name=name,
        picture_url=picture_url,
    )

    return user


async def create_conversation(
    db: AsyncSession,
    user_id: str,
) -> Conversation:
    conversation = Conversation(user_id=user_id)

    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)

    return conversation


def get_conversation_state(conversation: Conversation) -> ConversationState:
    return ConversationState(
        title=conversation.title,
        prompt_type=conversation.prompt_type,
        goal=conversation.goal,
        audience=conversation.audience,
        constraints=conversation.constraints or [],
        output_format=conversation.output_format,
        confidence=conversation.confidence or {},
        missing_fields=conversation.missing_fields or [],
        ready_to_finalize=conversation.ready_to_finalize,
    )


async def update_conversation_state(
    db: AsyncSession,
    conversation: Conversation,
    state: ConversationState,
) -> Conversation:
    conversation.goal = state.goal
    conversation.audience = state.audience
    conversation.constraints = state.constraints
    conversation.output_format = state.output_format
    conversation.prompt_type = state.prompt_type
    conversation.title = state.title
    conversation.confidence = state.confidence.model_dump()
    conversation.missing_fields = state.missing_fields
    conversation.ready_to_finalize = state.ready_to_finalize

    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)

    return conversation


async def get_conversation(
    db: AsyncSession,
    conversation_id: str,
    user_id: str,
) -> Conversation | None:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )

    return result.scalar_one_or_none()


async def get_conversations(
    db: AsyncSession,
    user_id: str,
    limit: int = 50,
) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
        .limit(limit)
    )

    return list(result.scalars().all())


async def enforce_rate_limit(
    db: AsyncSession,
    user_id: str,
    action: str,
    policies: list[RateLimitPolicy],
) -> None:
    active_policies = [
        policy
        for policy in policies
        if policy.max_requests > 0 and policy.window_seconds > 0
    ]

    if not active_policies:
        return

    now = datetime.now(timezone.utc)
    max_window_seconds = max(policy.window_seconds for policy in active_policies)
    cleanup_cutoff = now - timedelta(seconds=max_window_seconds)

    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
        {"lock_key": f"rate_limit:{action}:{user_id}"},
    )

    await db.execute(
        delete(RateLimitEvent).where(RateLimitEvent.created_at < cleanup_cutoff)
    )

    for policy in active_policies:
        cutoff = now - timedelta(seconds=policy.window_seconds)
        count_result = await db.execute(
            select(func.count())
            .select_from(RateLimitEvent)
            .where(
                RateLimitEvent.user_id == user_id,
                RateLimitEvent.action == action,
                RateLimitEvent.created_at >= cutoff,
            )
        )
        request_count = count_result.scalar_one()

        if request_count >= policy.max_requests:
            oldest_result = await db.execute(
                select(RateLimitEvent.created_at)
                .where(
                    RateLimitEvent.user_id == user_id,
                    RateLimitEvent.action == action,
                    RateLimitEvent.created_at >= cutoff,
                )
                .order_by(RateLimitEvent.created_at.asc())
                .limit(1)
            )
            oldest_event_at = oldest_result.scalar_one_or_none()
            retry_after_seconds = policy.window_seconds

            if oldest_event_at is not None:
                if oldest_event_at.tzinfo is None:
                    oldest_event_at = oldest_event_at.replace(tzinfo=timezone.utc)

                window_resets_at = oldest_event_at + timedelta(
                    seconds=policy.window_seconds
                )
                retry_after_seconds = max(
                    1,
                    int((window_resets_at - now).total_seconds()),
                )

            raise RateLimitExceeded(retry_after_seconds=retry_after_seconds)

    db.add(
        RateLimitEvent(
            user_id=user_id,
            action=action,
            created_at=now,
        )
    )
    await db.flush()


async def add_message(
    db: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
) -> Message:
    if role not in MESSAGE_ROLE_VALUES:
        raise ValueError(f"Invalid message role: {role}")

    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        created_at=datetime.now(timezone.utc),
    )

    db.add(message)
    await db.flush()
    await db.refresh(message)

    return message


async def create_final_prompt(
    db: AsyncSession,
    conversation_id: str,
    prompt: str,
    prompt_type: str,
    quality_score: int,
    review: PromptReview,
) -> FinalPrompt:
    final_prompt = FinalPrompt(
        conversation_id=conversation_id,
        prompt=prompt,
        prompt_type=prompt_type,
        quality_score=quality_score,
        review=review.model_dump(),
    )

    db.add(final_prompt)
    await db.flush()
    await db.refresh(final_prompt)

    return final_prompt


async def get_user_by_id(
    db: AsyncSession,
    user_id: str,
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    return result.scalar_one_or_none()


async def get_final_prompts(
    db: AsyncSession,
    conversation_id: str,
) -> list[FinalPrompt]:
    result = await db.execute(
        select(FinalPrompt)
        .where(FinalPrompt.conversation_id == conversation_id)
        .order_by(FinalPrompt.created_at.desc())
    )

    return list(result.scalars().all())


async def get_messages(
    db: AsyncSession,
    conversation_id: str,
    limit: int | None = None,
) -> list[Message]:
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
    )

    if limit is not None:
        query = query.limit(limit)

    result = await db.execute(query)

    messages = list(result.scalars().all())

    return list(reversed(messages))
