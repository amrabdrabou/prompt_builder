from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Conversation, Message, User
from schemas import ConversationState


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
        goal=conversation.goal,
        audience=conversation.audience,
        constraints=conversation.constraints or [],
        output_format=conversation.output_format,
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


async def add_message(
    db: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )

    db.add(message)
    await db.flush()
    await db.refresh(message)

    return message


async def get_user_by_id(
    db: AsyncSession,
    user_id: str,
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    return result.scalar_one_or_none()


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
