# Project Memory For Coding Agents

## Project

Prompt Builder is a FastAPI backend for a conversational prompt-building agent. The agent does not complete the user's original task. It asks clarifying questions, maintains structured state, and eventually returns a reviewed XML prompt.

Frontend is not implemented yet. `docker-compose.yml` keeps the frontend service behind the `frontend` profile.

## Current Architecture

- Backend: FastAPI, async SQLAlchemy, Alembic, PostgreSQL.
- Auth: Google OAuth via Authlib, JWT stored in an HTTP-only cookie.
- LLM: OpenAI Responses API, strict JSON schema, `store=False`.
- DB tables: `users`, `conversations`, `messages`, `final_prompts`, `rate_limit_events`, `alembic_version`.

Core files:
- `backend/main.py`: FastAPI app and `/chat`.
- `backend/agent.py`: OpenAI Responses call, validation retry, metadata-only logging.
- `backend/prompts.py`: Agent behavior and response contract.
- `backend/schemas.py`: API schemas, LLM schema, prompt review, XML validation.
- `backend/memory.py`: DB helpers for users, conversations, messages, final prompts.
- `backend/models.py`: SQLAlchemy models.
- `backend/config.py`: environment settings.

Authenticated API endpoints:
- `POST /chat`: send a user message, ask next question or return final prompt.
- `GET /conversations`: list the current user's conversations.
- `GET /conversations/{conversation_id}`: get one current-user-owned conversation and state.
- `GET /conversations/{conversation_id}/messages`: get messages for one current-user-owned conversation.
- `GET /conversations/{conversation_id}/final-prompts`: get saved final prompts for one current-user-owned conversation.

All conversation read endpoints must enforce ownership through `current_user.id`; guessed IDs from another user should return 404.

## Agent Flow

The agent workflow is:

```text
Analyze rough prompt
Extract known information
Update structured state
Identify missing information
Ask the next best question OR generate final prompt
Review final prompt quality
Fix once if backend validation fails
Persist state/messages/final prompt
Return result
```

Structured conversation state:
- `title`
- `prompt_type`: `writing`, `coding`, `marketing`, `analysis`, `research`, `planning`, `image_generation`, `automation`, `other`
- `goal`
- `audience`
- `constraints`
- `output_format`
- `confidence`: `goal`, `audience`, `constraints`, `output_format`
- `missing_fields`
- `ready_to_finalize`

Final prompt review:
- `is_clear`
- `uses_only_known_details`
- `is_xml_valid`
- `no_missing_critical_info`
- `ready_to_return`
- `quality_score`
- `missing_or_unclear_items`
- `fixes_applied`

Backend requires final prompts to have:
- valid XML
- root `<prompt>`
- non-empty tags: `role`, `goal`, `context`, `instructions`, `constraints`, `output_format`
- no unresolved placeholders such as `TODO`, `[insert...]`, `{{...}}`, `<...>`
- `quality_score >= 85`
- size limits for agent questions, suggestions, state text, review list items, and final prompts

Validation exists at multiple layers:
- FastAPI/Pydantic request and response schemas validate user input, UUID path params, agent output shape, prompt type, message role, quality score, XML structure, and output size limits.
- `memory.add_message()` rejects invalid message roles before any DB write.
- PostgreSQL check constraints enforce prompt type, message role, and final prompt quality-score bounds as a backstop.
- Every future project improvement should explicitly ask: what should be validated at the API/schema layer, business-logic layer, DB layer, and test layer?

## Cost, Security, Privacy

- Do not add extra model calls by default. The normal flow should use one LLM call per user turn.
- One optional repair attempt is allowed only if the LLM response fails JSON/schema validation.
- `/chat` has database-backed per-user rate limiting before the OpenAI call. Defaults are 10 requests/minute and 100 requests/hour; set max requests to `0` to disable a policy in local testing only. Enforcement uses a PostgreSQL advisory transaction lock per user/action to avoid parallel requests bypassing the count.
- OpenAI calls should use `store=False` where supported by the API call being used.
- Logs must not include user messages, final prompts, secrets, OAuth data, JWTs, cookies, authorization headers, or database URLs.
- Metadata logging is allowed: model name, action type, prompt category/type, latency, token counts, response status, and validation errors without raw content.
- Do not ask users for sensitive personal data unless the prompt explicitly requires it.
- If a prompt request touches health, legal, financial, identity, or other sensitive areas, ask only for the minimum necessary details and avoid collecting unnecessary personal information.
- Never expose internal error details to the frontend. Log safe debugging metadata on the backend instead.
- Keep API keys and secrets only in environment variables or secret managers, never in frontend code or committed files.

## Commands

Run backend tests:

```bash
cd backend
../backend/.venv/bin/python -m unittest discover -s tests
```

Compile check:

```bash
backend/.venv/bin/python -m compileall backend -q
```

Check app import and OpenAPI generation:

```bash
cd backend
../backend/.venv/bin/python -c "from main import app; schema=app.openapi(); print(app.title); print(sorted(schema.get('components', {}).get('schemas', {}).keys()))"
```

Run migrations from host against the Compose-mapped DB:

```bash
cd backend
DATABASE_URL='postgresql+psycopg://amora:Sommar26@localhost:5433/prompt_builder' ../backend/.venv/bin/alembic upgrade head
```

Check current DB revision:

```bash
cd backend
DATABASE_URL='postgresql+psycopg://amora:Sommar26@localhost:5433/prompt_builder' ../backend/.venv/bin/alembic current
```

## Important Local Gotchas

- `backend/.env` may use `postgres` as DB host. That works inside Docker Compose, not from the host shell. Use `localhost:5433` override from host.
- Docker socket access may be blocked in the agent shell.
- If permissions block an important command or file operation, do not burn time trying to route around it. Explain the blocker clearly and ask the user to help manually or grant permission.
- `backend/venv/`, `backend/.venv/`, and migration `__pycache__` are ignored.
- `CLAUDE.md` exists but is stale; prefer this `AGENTS.md`.
- Update this `AGENTS.md` every time project behavior, architecture, commands, endpoints, tests, migrations, or important lessons change. Treat it as shared project memory for future sessions.

## Verification Checklist For Agent Changes

When changing schemas, prompts, OpenAI calls, or migrations, verify:

```text
Pydantic validation tests
Generated OpenAI JSON schema
FastAPI OpenAPI generation
Python compileall
Alembic head/current
DB schema if migrations changed
```

Regression learned: do not only test Pydantic models. Generated JSON schema matters. A previous metadata-stripper bug removed the real `title` field because JSON Schema also uses `title` as metadata; keep the schema regression test.

Validation learned: when adding endpoints or persistence fields, validate early and also add a database backstop when the field has a small allowed set or numeric range. For this app, UUID path params should be typed as `UUID`, roles should stay `user`/`assistant`, prompt types should stay in the known prompt-type set, and final prompt quality scores should stay in `0..100`.

Mocked `/chat` endpoint tests exist in `backend/tests/test_chat_endpoint.py`. They override auth and the agent, use isolated test rows in the local Postgres DB, and spend zero OpenAI tokens. They cover:
- ask-question flow
- final-prompt flow
- existing conversation state being passed back into the agent
- state persistence
- user/assistant message persistence
- final prompt persistence
- per-user `/chat` rate limiting returning 429 before the fake agent/OpenAI boundary
- frontend read endpoints for conversations, messages, and final prompts
- 404 ownership protection for other users' conversations
- 422 validation for malformed conversation UUIDs on read endpoints

Regression learned: message ordering cannot rely only on Postgres `now()` timestamps when user and assistant messages are inserted in the same transaction. `memory.add_message()` sets a Python UTC `created_at` timestamp per message to keep history order stable.

## Lessons Learned From Tests

- Unit tests alone are not enough for this app. The route-level `/chat` tests caught a real persistence/history-ordering bug that schema tests could not catch.
- Mock external boundaries aggressively: fake auth and fake agent/OpenAI responses. This gives high confidence without spending OpenAI tokens or requiring Google OAuth.
- Test both response shape and persisted DB state. For `/chat`, assert the HTTP response, `conversations` state fields, `messages`, and `final_prompts`.
- Existing-conversation tests are essential. They verify that persisted state is loaded and passed back into the agent on the next turn.
- Generated schemas are part of the product. Always inspect/test `AGENT_LLM_RESPONSE_JSON_SCHEMA` after changing Pydantic models.
- Validation is part of the feature, not a final cleanup step. New behavior should come with request/schema validation, persistence validation when relevant, DB constraints for stable invariants, and regression tests.
- Beware DB timestamp precision and transaction semantics. If order matters, set explicit timestamps or add a deterministic ordering column.
- Keep tests privacy-safe: do not use real user data, API keys, OAuth tokens, cookies, or live OpenAI calls.
- Abuse protection should run before expensive external calls. For `/chat`, assert the rate-limited path does not call the fake agent.

## Next Improvements

Highest-value improvements to consider next:

1. Build a larger eval fixture set with 20-50 conversation scenarios: vague request asks a question, clear request finalizes, sensitive request avoids unnecessary personal data, final prompt does not invent facts, refine request revises an existing prompt.
2. Add production config safety checks for secure cookies, strong secrets, and CORS origins from environment variables.
3. Add token budget guardrails before OpenAI calls: cap history, cap final prompt size, and consider summarizing older messages later.
4. Add frontend contract docs for `/chat`, auth, conversation state, read endpoints, and final prompt responses.
5. Add `/health` and `/ready` endpoints. `/ready` should check DB connectivity and required config without exposing secrets.
6. Decide refresh/session strategy for JWT cookie expiry.
7. Improve final prompt version UX with named versions such as original, shortened, JSON format, or more detailed.

Recommended next task: larger eval fixture set. The mocked `/chat` tests now cover route/persistence regressions; eval fixtures should cover agent behavior expectations.
