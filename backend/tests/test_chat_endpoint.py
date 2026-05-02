import uuid
import unittest

import httpx
from sqlalchemy import delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import main
from config import settings
from models import Conversation, FinalPrompt, Message, RateLimitEvent, User
from schemas import AgentLLMResponse, ConversationState, PromptReview


def get_host_test_database_url() -> str:
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required for /chat endpoint tests.")

    url = make_url(settings.DATABASE_URL)

    if url.host == "postgres":
        url = url.set(host="localhost", port=5433)

    return url.render_as_string(hide_password=False)


def reviewed_prompt_response(
    *,
    prompt_type: str = "writing",
    title: str = "Summary Prompt",
) -> AgentLLMResponse:
    return AgentLLMResponse(
        action="final_prompt",
        message="",
        suggestions=[],
        prompt=(
            "<prompt>"
            "<role>Act as a concise writing assistant.</role>"
            "<goal>Create a short summary.</goal>"
            "<context>The user wants a prompt that summarizes supplied text.</context>"
            "<instructions>Write clearly and preserve the important points.</instructions>"
            "<constraints>Do not invent details.</constraints>"
            "<output_format>Return three bullet points.</output_format>"
            "</prompt>"
        ),
        conversation_state=ConversationState(
            title=title,
            prompt_type=prompt_type,
            goal="Create a short summary prompt",
            audience="General readers",
            constraints=["Do not invent details"],
            output_format="Three bullet points",
            confidence={
                "goal": 95,
                "audience": 80,
                "constraints": 90,
                "output_format": 95,
            },
            missing_fields=[],
            ready_to_finalize=True,
        ),
        prompt_review=PromptReview(
            is_clear=True,
            uses_only_known_details=True,
            is_xml_valid=True,
            no_missing_critical_info=True,
            ready_to_return=True,
            quality_score=92,
        ),
    )


class FakeAgent:
    def __init__(self, responses: list[AgentLLMResponse]):
        self.responses = responses
        self.calls = []

    async def run(self, conversation_messages, conversation_state, user_id):
        self.calls.append(
            {
                "conversation_messages": conversation_messages,
                "conversation_state": conversation_state,
                "user_id": user_id,
            }
        )

        return self.responses.pop(0)


class ChatEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        database_url = get_host_test_database_url()
        self.engine = create_async_engine(database_url)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
        )
        self.user_id = f"test-user-{uuid.uuid4()}"
        self.extra_user_ids = []
        self.user = User(
            id=self.user_id,
            google_sub=f"google-{self.user_id}",
            email=f"{self.user_id}@example.test",
            name="Test User",
        )

        try:
            async with self.SessionLocal() as session:
                session.add(self.user)
                await session.commit()
        except OperationalError as error:
            await self.engine.dispose()
            self.skipTest(f"Local test database is not available: {error}")

        async def override_get_db():
            async with self.SessionLocal() as session:
                yield session

        async def override_get_current_user():
            return self.user

        self.fake_agent = FakeAgent([])

        def override_get_agent():
            return self.fake_agent

        main.app.dependency_overrides[main.get_db] = override_get_db
        main.app.dependency_overrides[main.get_current_user] = override_get_current_user
        main.app.dependency_overrides[main.get_agent] = override_get_agent

        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        main.app.dependency_overrides.clear()

        async with self.SessionLocal() as session:
            await session.execute(
                delete(User).where(User.id.in_([self.user_id, *self.extra_user_ids]))
            )
            await session.commit()

        await self.engine.dispose()

    async def test_chat_ask_question_flow_persists_messages_and_state(self):
        self.fake_agent.responses = [
            AgentLLMResponse(
                action="ask_question",
                message="Who is the audience for this prompt?",
                suggestions=["Developers", "Students", "Managers"],
                prompt="",
                conversation_state=ConversationState(
                    title="Summary Prompt",
                    prompt_type="writing",
                    goal="Create a summary prompt",
                    audience="",
                    constraints=["Keep it concise"],
                    output_format="",
                    confidence={
                        "goal": 85,
                        "audience": 0,
                        "constraints": 70,
                        "output_format": 0,
                    },
                    missing_fields=["Audience", "Output format"],
                    ready_to_finalize=False,
                ),
                prompt_review=PromptReview(),
            )
        ]

        response = await self.client.post(
            "/chat",
            json={"user_message": "Help me write a prompt for summarizing text."},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        conversation_id = body["conversation_id"]

        self.assertEqual(body["action"], "ask_question")
        self.assertEqual(body["message"], "Who is the audience for this prompt?")
        self.assertEqual(body["conversation_state"]["title"], "Summary Prompt")

        async with self.SessionLocal() as session:
            conversation = await session.get(Conversation, conversation_id)
            self.assertIsNotNone(conversation)
            self.assertEqual(conversation.user_id, self.user_id)
            self.assertEqual(conversation.title, "Summary Prompt")
            self.assertEqual(conversation.prompt_type, "writing")
            self.assertEqual(conversation.goal, "Create a summary prompt")
            self.assertEqual(conversation.missing_fields, ["Audience", "Output format"])
            self.assertFalse(conversation.ready_to_finalize)

            messages = (
                await session.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at)
                )
            ).scalars().all()

            self.assertEqual([message.role for message in messages], ["user", "assistant"])
            self.assertEqual(messages[1].content, "Who is the audience for this prompt?")

        self.assertEqual(len(self.fake_agent.calls), 1)
        self.assertEqual(self.fake_agent.calls[0]["user_id"], self.user_id)
        self.assertEqual(
            self.fake_agent.calls[0]["conversation_messages"][0]["content"],
            "Help me write a prompt for summarizing text.",
        )

    async def test_chat_final_prompt_flow_persists_state_and_final_prompt(self):
        self.fake_agent.responses = [reviewed_prompt_response()]

        response = await self.client.post(
            "/chat",
            json={"user_message": "Create a prompt that summarizes an article in bullets."},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        conversation_id = body["conversation_id"]
        prompt_id = body["prompt_id"]

        self.assertEqual(body["action"], "final_prompt")
        self.assertEqual(body["prompt_review"]["quality_score"], 92)
        self.assertIn("<prompt>", body["prompt"])

        async with self.SessionLocal() as session:
            conversation = await session.get(Conversation, conversation_id)
            final_prompt = await session.get(FinalPrompt, prompt_id)

            self.assertIsNotNone(conversation)
            self.assertIsNotNone(final_prompt)
            self.assertEqual(conversation.ready_to_finalize, True)
            self.assertEqual(conversation.prompt_type, "writing")
            self.assertEqual(final_prompt.conversation_id, conversation_id)
            self.assertEqual(final_prompt.prompt_type, "writing")
            self.assertEqual(final_prompt.quality_score, 92)
            self.assertEqual(final_prompt.review["ready_to_return"], True)

            messages = (
                await session.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at)
                )
            ).scalars().all()

            self.assertEqual([message.role for message in messages], ["user", "assistant"])
            self.assertEqual(messages[1].content, final_prompt.prompt)

    async def test_chat_existing_conversation_passes_persisted_state_to_agent(self):
        self.fake_agent.responses = [
            AgentLLMResponse(
                action="ask_question",
                message="What output format should the summary use?",
                suggestions=["Bullets", "Paragraph", "Checklist"],
                prompt="",
                conversation_state=ConversationState(
                    title="Summary Prompt",
                    prompt_type="writing",
                    goal="Create a summary prompt",
                    audience="General readers",
                    constraints=["Keep it concise"],
                    output_format="",
                    confidence={
                        "goal": 90,
                        "audience": 80,
                        "constraints": 75,
                        "output_format": 0,
                    },
                    missing_fields=["Output format"],
                    ready_to_finalize=False,
                ),
                prompt_review=PromptReview(),
            ),
            reviewed_prompt_response(title="Summary Prompt"),
        ]

        first_response = await self.client.post(
            "/chat",
            json={"user_message": "Create a summary prompt for general readers."},
        )
        conversation_id = first_response.json()["conversation_id"]

        second_response = await self.client.post(
            "/chat",
            json={
                "conversation_id": conversation_id,
                "user_message": "Use three bullet points.",
            },
        )

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.json()["action"], "final_prompt")
        self.assertEqual(len(self.fake_agent.calls), 2)

        second_call = self.fake_agent.calls[1]
        self.assertEqual(second_call["conversation_state"].goal, "Create a summary prompt")
        self.assertEqual(second_call["conversation_state"].audience, "General readers")
        self.assertEqual(second_call["conversation_state"].missing_fields, ["Output format"])
        self.assertEqual(
            [message["role"] for message in second_call["conversation_messages"]],
            ["user", "assistant", "user"],
        )

        async with self.SessionLocal() as session:
            final_prompts = (
                await session.execute(
                    select(FinalPrompt).where(
                        FinalPrompt.conversation_id == conversation_id
                    )
                )
            ).scalars().all()

            self.assertEqual(len(final_prompts), 1)

    async def test_chat_rate_limit_blocks_before_agent_call(self):
        old_short_max = settings.CHAT_RATE_LIMIT_SHORT_MAX_REQUESTS
        old_short_window = settings.CHAT_RATE_LIMIT_SHORT_WINDOW_SECONDS
        old_long_max = settings.CHAT_RATE_LIMIT_LONG_MAX_REQUESTS

        settings.CHAT_RATE_LIMIT_SHORT_MAX_REQUESTS = 1
        settings.CHAT_RATE_LIMIT_SHORT_WINDOW_SECONDS = 60
        settings.CHAT_RATE_LIMIT_LONG_MAX_REQUESTS = 0

        try:
            self.fake_agent.responses = [
                reviewed_prompt_response(),
                reviewed_prompt_response(),
            ]

            first_response = await self.client.post(
                "/chat",
                json={"user_message": "Create a prompt that summarizes an article."},
            )
            self.assertEqual(first_response.status_code, 200)

            second_response = await self.client.post(
                "/chat",
                json={"user_message": "Create another prompt."},
            )

            self.assertEqual(second_response.status_code, 429)
            self.assertEqual(
                second_response.json()["detail"],
                "Too many chat requests. Please try again shortly.",
            )
            self.assertIn("retry-after", second_response.headers)
            self.assertEqual(len(self.fake_agent.calls), 1)

            async with self.SessionLocal() as session:
                events = (
                    await session.execute(
                        select(RateLimitEvent).where(
                            RateLimitEvent.user_id == self.user_id,
                            RateLimitEvent.action == "chat",
                        )
                    )
                ).scalars().all()

                self.assertEqual(len(events), 1)
        finally:
            settings.CHAT_RATE_LIMIT_SHORT_MAX_REQUESTS = old_short_max
            settings.CHAT_RATE_LIMIT_SHORT_WINDOW_SECONDS = old_short_window
            settings.CHAT_RATE_LIMIT_LONG_MAX_REQUESTS = old_long_max

    async def test_read_endpoints_return_user_owned_conversation_data(self):
        self.fake_agent.responses = [reviewed_prompt_response()]

        chat_response = await self.client.post(
            "/chat",
            json={"user_message": "Create a prompt that summarizes an article in bullets."},
        )
        self.assertEqual(chat_response.status_code, 200)

        chat_body = chat_response.json()
        conversation_id = chat_body["conversation_id"]
        prompt_id = chat_body["prompt_id"]

        list_response = await self.client.get("/conversations")
        self.assertEqual(list_response.status_code, 200)
        conversations = list_response.json()
        self.assertTrue(
            any(conversation["id"] == conversation_id for conversation in conversations)
        )

        detail_response = await self.client.get(f"/conversations/{conversation_id}")
        self.assertEqual(detail_response.status_code, 200)
        detail = detail_response.json()
        self.assertEqual(detail["id"], conversation_id)
        self.assertEqual(detail["conversation_state"]["goal"], "Create a short summary prompt")

        messages_response = await self.client.get(
            f"/conversations/{conversation_id}/messages"
        )
        self.assertEqual(messages_response.status_code, 200)
        messages = messages_response.json()
        self.assertEqual([message["role"] for message in messages], ["user", "assistant"])

        prompts_response = await self.client.get(
            f"/conversations/{conversation_id}/final-prompts"
        )
        self.assertEqual(prompts_response.status_code, 200)
        final_prompts = prompts_response.json()
        self.assertEqual(len(final_prompts), 1)
        self.assertEqual(final_prompts[0]["id"], prompt_id)
        self.assertEqual(final_prompts[0]["quality_score"], 92)

    async def test_read_endpoints_return_404_for_other_users_conversation(self):
        other_user_id = f"other-user-{uuid.uuid4()}"
        self.extra_user_ids.append(other_user_id)

        async with self.SessionLocal() as session:
            other_user = User(
                id=other_user_id,
                google_sub=f"google-{other_user_id}",
                email=f"{other_user_id}@example.test",
                name="Other User",
            )
            other_conversation = Conversation(
                user_id=other_user_id,
                title="Private Conversation",
                prompt_type="writing",
            )
            session.add_all([other_user, other_conversation])
            await session.commit()
            await session.refresh(other_conversation)
            other_conversation_id = other_conversation.id

        endpoints = [
            f"/conversations/{other_conversation_id}",
            f"/conversations/{other_conversation_id}/messages",
            f"/conversations/{other_conversation_id}/final-prompts",
        ]

        for endpoint in endpoints:
            response = await self.client.get(endpoint)
            self.assertEqual(response.status_code, 404)

    async def test_read_endpoints_reject_invalid_conversation_ids(self):
        endpoints = [
            "/conversations/not-a-uuid",
            "/conversations/not-a-uuid/messages",
            "/conversations/not-a-uuid/final-prompts",
        ]

        for endpoint in endpoints:
            response = await self.client.get(endpoint)
            self.assertEqual(response.status_code, 422)
