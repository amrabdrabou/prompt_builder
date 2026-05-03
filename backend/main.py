import asyncio
import json
import logging
from functools import lru_cache
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from starlette.middleware.sessions import SessionMiddleware

from agent import PromptBuilderAgent
from auth import get_current_user, router as auth_router
from config import settings
from database import get_db
from logging_config import setup_logging
from memory import (
    add_message,
    create_conversation,
    create_final_prompt,
    enforce_rate_limit,
    get_conversation,
    get_conversation_state,
    get_conversations,
    get_final_prompts,
    get_messages,
    RateLimitExceeded,
    RateLimitPolicy,
    update_conversation_state,
)
from models import Conversation, FinalPrompt, Message, User
from schemas import (
    AgentLLMResponse,
    AskQuestionResponse,
    ChatRequest,
    ConversationDetailResponse,
    ConversationSummaryResponse,
    ConversationState,
    FinalPromptResponse,
    FinalPromptRecordResponse,
    MessageResponse,
)


setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(title="Prompt Builder Agent API")

if not settings.SESSION_SECRET_KEY:
    raise RuntimeError("SESSION_SECRET_KEY is missing. Add it to backend/.env")

if not settings.AUTH_COOKIE_SECURE:
    logger.warning(
        "AUTH_COOKIE_SECURE is False — auth cookies are not marked Secure. "
        "Set AUTH_COOKIE_SECURE=True in production."
    )

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@lru_cache
def get_agent() -> PromptBuilderAgent:
    return PromptBuilderAgent()


def get_chat_rate_limit_policies() -> list[RateLimitPolicy]:
    return [
        RateLimitPolicy(
            max_requests=settings.CHAT_RATE_LIMIT_SHORT_MAX_REQUESTS,
            window_seconds=settings.CHAT_RATE_LIMIT_SHORT_WINDOW_SECONDS,
        ),
        RateLimitPolicy(
            max_requests=settings.CHAT_RATE_LIMIT_LONG_MAX_REQUESTS,
            window_seconds=settings.CHAT_RATE_LIMIT_LONG_WINDOW_SECONDS,
        ),
    ]


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


CHAT_PROGRESS_STEPS = (
    "Reading your request",
    "Checking the conversation state",
    "Finding the next missing detail",
    "Preparing a clean response",
)


@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "message": "Prompt Builder Agent backend is running",
    }


def to_conversation_summary(
    conversation: Conversation,
) -> ConversationSummaryResponse:
    return ConversationSummaryResponse(
        id=conversation.id,
        title=conversation.title,
        prompt_type=conversation.prompt_type,
        ready_to_finalize=conversation.ready_to_finalize,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def to_conversation_detail(
    conversation: Conversation,
) -> ConversationDetailResponse:
    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        prompt_type=conversation.prompt_type,
        conversation_state=get_conversation_state(conversation),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def to_message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
    )


def to_final_prompt_response(
    final_prompt: FinalPrompt,
) -> FinalPromptRecordResponse:
    return FinalPromptRecordResponse(
        id=final_prompt.id,
        conversation_id=final_prompt.conversation_id,
        prompt=final_prompt.prompt,
        prompt_type=final_prompt.prompt_type,
        quality_score=final_prompt.quality_score,
        review=final_prompt.review,
        created_at=final_prompt.created_at,
    )


@app.get("/conversations", response_model=list[ConversationSummaryResponse])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversations = await get_conversations(
        db=db,
        user_id=current_user.id,
    )

    return [
        to_conversation_summary(conversation)
        for conversation in conversations
    ]


@app.post(
    "/conversations",
    response_model=ConversationDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_empty_conversation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = await create_conversation(
        db=db,
        user_id=current_user.id,
    )
    await db.commit()

    return to_conversation_detail(conversation)


@app.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def read_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = await get_conversation(
        db=db,
        conversation_id=str(conversation_id),
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return to_conversation_detail(conversation)


@app.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def read_conversation_messages(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = await get_conversation(
        db=db,
        conversation_id=str(conversation_id),
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    messages = await get_messages(
        db=db,
        conversation_id=conversation.id,
    )

    return [
        to_message_response(message)
        for message in messages
    ]


@app.get(
    "/conversations/{conversation_id}/final-prompts",
    response_model=list[FinalPromptRecordResponse],
)
async def read_conversation_final_prompts(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = await get_conversation(
        db=db,
        conversation_id=str(conversation_id),
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    final_prompts = await get_final_prompts(
        db=db,
        conversation_id=conversation.id,
    )

    return [
        to_final_prompt_response(final_prompt)
        for final_prompt in final_prompts
    ]


@app.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    agent: PromptBuilderAgent = Depends(get_agent),
    current_user: User = Depends(get_current_user),
):
    # ── Pre-streaming: resolve conversation and enforce rate limit ──────────
    conversation = None

    if request.conversation_id:
        conversation = await get_conversation(
            db=db,
            conversation_id=str(request.conversation_id),
            user_id=current_user.id,
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )

        db_messages = await get_messages(
            db=db,
            conversation_id=conversation.id,
            limit=settings.MAX_HISTORY_MESSAGES,
        )
    else:
        db_messages = []

    conversation_state = (
        get_conversation_state(conversation)
        if conversation is not None
        else ConversationState()
    )

    try:
        await enforce_rate_limit(
            db=db,
            user_id=current_user.id,
            action="chat",
            policies=get_chat_rate_limit_policies(),
        )
        await db.commit()
    except RateLimitExceeded as error:
        await db.rollback()
        logger.warning(
            "Rate limit exceeded",
            extra={
                "user_id": current_user.id,
                "action": "chat",
                "retry_after_seconds": error.retry_after_seconds,
            },
        )
        raise HTTPException(
            status_code=429,
            detail="Too many chat requests. Please try again shortly.",
            headers={"Retry-After": str(error.retry_after_seconds)},
        ) from error

    conversation_messages = [
        {"role": m.role, "content": m.content}
        for m in db_messages
    ]
    conversation_messages.append({"role": "user", "content": request.user_message})

    # ── Streaming generator ─────────────────────────────────────────────────
    async def generate():
        nonlocal conversation
        try:
            for step in CHAT_PROGRESS_STEPS:
                yield _sse({"type": "status", "message": step})
                await asyncio.sleep(0.05)

            async for item in agent.stream_run(
                conversation_messages=conversation_messages,
                conversation_state=conversation_state,
                user_id=current_user.id,
            ):
                if isinstance(item, str):
                    yield _sse({"type": "text_delta", "text": item})
                    continue

                # Final item: AgentLLMResponse — persist then emit done event
                llm_response: AgentLLMResponse = item
                yield _sse({"type": "status", "message": "Saving the conversation"})

                if conversation is None:
                    conversation = await create_conversation(
                        db=db,
                        user_id=current_user.id,
                    )

                await add_message(
                    db=db,
                    conversation_id=conversation.id,
                    role="user",
                    content=request.user_message,
                )

                await update_conversation_state(
                    db=db,
                    conversation=conversation,
                    state=llm_response.conversation_state,
                )

                if llm_response.action == "ask_question":
                    await add_message(
                        db=db,
                        conversation_id=conversation.id,
                        role="assistant",
                        content=llm_response.message,
                    )
                    await db.commit()

                    response_obj = AskQuestionResponse(
                        action="ask_question",
                        conversation_id=conversation.id,
                        message=llm_response.message,
                        suggestions=llm_response.suggestions,
                        conversation_state=llm_response.conversation_state,
                    )
                    yield _sse({"type": "ask_question", **response_obj.model_dump(mode="json")})

                elif llm_response.action == "final_prompt":
                    final_prompt = await create_final_prompt(
                        db=db,
                        conversation_id=conversation.id,
                        prompt=llm_response.prompt,
                        prompt_type=llm_response.conversation_state.prompt_type,
                        quality_score=llm_response.prompt_review.quality_score,
                        review=llm_response.prompt_review,
                    )
                    await add_message(
                        db=db,
                        conversation_id=conversation.id,
                        role="assistant",
                        content=llm_response.prompt,
                    )
                    await db.commit()

                    response_obj = FinalPromptResponse(
                        action="final_prompt",
                        conversation_id=conversation.id,
                        prompt_id=final_prompt.id,
                        prompt=llm_response.prompt,
                        conversation_state=llm_response.conversation_state,
                        prompt_review=llm_response.prompt_review,
                    )
                    yield _sse({"type": "final_prompt", **response_obj.model_dump(mode="json")})

        except Exception:
            await db.rollback()
            logger.exception("Unexpected error in chat stream")
            yield _sse({"type": "error", "detail": "Something went wrong while processing the chat request."})

    return StreamingResponse(generate(), media_type="text/event-stream")
