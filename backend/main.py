import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from starlette.middleware.sessions import SessionMiddleware

from auth import router as auth_router
from config import settings
from schemas import UserResponse
from agent import PromptBuilderAgent
from database import get_db
from memory import add_message, create_conversation, get_conversation, get_messages
from schemas import AgentResponse, AskQuestionResponse, ChatRequest, FinalPromptResponse

from functools import lru_cache
from config import settings
from logging_config import setup_logging

from auth import get_current_user, router as auth_router
from models import User


setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(title="Prompt Builder Agent API")

if not settings.SESSION_SECRET_KEY:
    raise RuntimeError("SESSION_SECRET_KEY is missing. Add it to backend/.env")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@lru_cache
def get_agent() -> PromptBuilderAgent:
    return PromptBuilderAgent()

@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "message": "Prompt Builder Agent backend is running",
    }


@app.post("/chat", response_model=AgentResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    agent: PromptBuilderAgent = Depends(get_agent),
    current_user: User = Depends(get_current_user),
):
    try:
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

        conversation_messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in db_messages
        ]

        conversation_messages.append(
            {
                "role": "user",
                "content": request.user_message,
            }
        )

        llm_response = await agent.run(conversation_messages)

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

        if llm_response.action == "ask_question":
            await add_message(
                db=db,
                conversation_id=conversation.id,
                role="assistant",
                content=llm_response.message,
            )

            await db.commit()

            return AskQuestionResponse(
                action="ask_question",
                conversation_id=conversation.id,
                message=llm_response.message,
                suggestions=llm_response.suggestions,
            )

        if llm_response.action == "final_prompt":
            await add_message(
                db=db,
                conversation_id=conversation.id,
                role="assistant",
                content=llm_response.prompt,
            )

            await db.commit()

            return FinalPromptResponse(
                action="final_prompt",
                conversation_id=conversation.id,
                prompt=llm_response.prompt,
            )

        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unknown agent action.",
        )

    except HTTPException:
        await db.rollback()
        raise

    except Exception as error:
        await db.rollback()

        logger.exception("Unexpected error while processing chat request")

        raise HTTPException(
            status_code=500,
            detail="Something went wrong while processing the chat request.",
        ) from error