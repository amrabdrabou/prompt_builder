# Project Memory For Coding Agents

## Purpose

Prompt Builder is a conversational prompt-building product. The assistant does not complete the user's original task directly; it asks clarifying questions, maintains structured conversation state, and eventually returns a reviewed XML prompt.

Keep `AGENTS.md` and `CLAUDE.md` in sync whenever architecture, commands, endpoints, validation rules, migrations, or major workflow lessons change.

## Architecture

- Backend: FastAPI, async SQLAlchemy, Alembic, PostgreSQL.
- Frontend: Vite, React, TypeScript, Tailwind CSS.
- Auth: Google OAuth through Authlib. JWTs are stored only in HTTP-only cookies.
- LLM: OpenAI Responses API with strict JSON schema, `store=False`, and `stream=True`.
- Streaming behavior: `/chat` returns SSE. The backend buffers and validates the full JSON response, then replays `ask_question` text word-by-word to the frontend. This is a UX animation, not true time-to-first-token streaming.
- Database tables: `users`, `conversations`, `messages`, `final_prompts`, `rate_limit_events`, `alembic_version`.

## Important Files

- `backend/main.py`: FastAPI app, auth routes, conversation routes, `/chat` SSE endpoint.
- `backend/agent.py`: OpenAI Responses call, schema validation retry, metadata-only logging.
- `backend/prompts.py`: Agent instructions and response contract.
- `backend/schemas.py`: API schemas, LLM schema, prompt review, XML validation.
- `backend/memory.py`: Database helpers for users, conversations, messages, and final prompts.
- `backend/models.py`: SQLAlchemy models.
- `backend/config.py`: Environment settings.
- `frontend/src/App.tsx`: Route/auth gate and workspace composition.
- `frontend/src/api/`: Authenticated fetch client, auth helpers, chat SSE client, conversation API helpers.
- `frontend/src/hooks/`: Auth/session, path routing, chat streaming, conversation loading.
- `frontend/src/pages/auth/AuthPage.tsx`: Shared login/register page. Both modes use Google OAuth.
- `frontend/src/components/auth/`: Auth layout and Google sign-in components.
- `frontend/src/components/layout/`: App shell and sidebar layout.
- `frontend/src/components/start/`: Authenticated start page and prompt starter controls.
- `frontend/src/components/chat/`: Conversation workspace, message thread, composer, suggestions, intelligence panel, final prompt card.
- `frontend/src/components/ui/`: Shared UI primitives.
- `frontend/src/types/index.ts`: Frontend API and UI types.
- `scripts/validate.sh`: Full local validation workflow.

## API Contract

Authenticated endpoints:

- `GET /auth/me`: Return the current user from the auth cookie.
- `POST /auth/logout`: Clear the auth cookie.
- `GET /auth/google/login`: Redirect to Google OAuth.
- `GET /auth/google/callback`: Create or load the Google user, set the auth cookie, redirect to the frontend.
- `GET /conversations`: List current-user conversations.
- `POST /conversations`: Create an empty current-user conversation and return its initial state.
- `GET /conversations/{conversation_id}`: Return one current-user conversation and state.
- `GET /conversations/{conversation_id}/messages`: Return messages for one current-user conversation.
- `GET /conversations/{conversation_id}/final-prompts`: Return saved final prompts for one current-user conversation.
- `POST /chat`: Send a user message and stream safe progress plus the final agent result as SSE.

`/chat` SSE events:

- `status`: Safe progress label for the frontend activity timeline.
- `text_delta`: Word chunks for `ask_question` replay.
- `ask_question`: Done event when the agent needs more information.
- `final_prompt`: Done event when the agent returns the reviewed XML prompt.
- `error`: Safe frontend error message.

All conversation reads must enforce ownership with `current_user.id`. Guessed conversation IDs from another user should return `404`.

## Agent Behavior

Normal workflow:

```text
Analyze rough prompt
Extract known information
Update structured state
Identify missing information
Ask the next best question OR generate final prompt
Review final prompt quality
Repair once if backend validation fails
Persist state/messages/final prompt
Return result
```

Conversation state fields:

- `title`
- `prompt_type`: `writing`, `coding`, `marketing`, `analysis`, `research`, `planning`, `image_generation`, `automation`, `other`
- `goal`
- `audience`
- `constraints`
- `output_format`
- `confidence`: `goal`, `audience`, `constraints`, `output_format`
- `missing_fields`
- `ready_to_finalize`

Final prompt review fields:

- `is_clear`
- `uses_only_known_details`
- `is_xml_valid`
- `no_missing_critical_info`
- `ready_to_return`
- `quality_score`
- `missing_or_unclear_items`
- `fixes_applied`

Final prompts must:

- Be valid XML with root `<prompt>`.
- Include non-empty `role`, `goal`, `context`, `instructions`, `constraints`, and `output_format` tags.
- Avoid unresolved placeholders such as `TODO`, `[insert...]`, `{{...}}`, and generic `<...>`.
- Have `quality_score >= 85`.
- Respect schema size limits for questions, suggestions, state text, review items, and final prompt text.

## Validation And Safety Rules

- Validate early at the API/schema layer, business-logic layer, database layer, and test layer.
- Use typed UUID path params for conversation routes.
- Keep message roles limited to `user` and `assistant`.
- Keep prompt types limited to the known prompt-type set.
- Keep final prompt quality scores within `0..100`.
- `memory.add_message()` must reject invalid message roles before DB writes.
- PostgreSQL check constraints should backstop stable small enums and numeric ranges.
- Generated OpenAI JSON schema is part of the product contract; test it when Pydantic models change.
- Do not add extra model calls by default. The normal flow should use one LLM call per user turn.
- One repair attempt is allowed only when the LLM response fails JSON/schema validation.
- `/chat` rate limiting must run before any OpenAI call.
- History trimming is character-count based through `MAX_HISTORY_CHARS`; preserve the current user turn.
- OpenAI calls should use `store=False` when supported.
- Logs must never include user messages, final prompts, secrets, OAuth data, JWTs, cookies, authorization headers, or database URLs.
- Metadata-only logging is allowed: model, action type, prompt type, latency, token counts, response status, and validation errors without raw content.
- Never expose internal error details to the frontend.
- Keep secrets in environment variables or secret managers, never frontend code or committed files.

## Frontend Rules

- Frontend auth is Google OAuth only. Do not add email/password UI without backend endpoints, schemas, persistence, validation, and tests.
- Requests use `credentials: "include"` for HTTP-only cookie auth. Never store JWTs in frontend state or localStorage.
- Keep conversation fetching behind the auth gate. Unauthenticated users should call `/auth/me` only, not conversation endpoints.
- Routing is intentionally lightweight in `frontend/src/hooks/useRoute.ts`; add React Router only if navigation complexity clearly requires it.
- Auth routes are `/login` and `/register`; authenticated routes are `/` and `/c/{conversation_id}`.
- Start-page submission first calls `POST /conversations`, navigates to `/c/{conversation_id}`, then sends `/chat`.
- The "Generate Lazy Prompt" action should finalize from known information without inventing specific facts.
- Follow `DESIGN.md`: near-black canvas, charcoal surfaces, hairline borders, ink text tokens, lavender-blue accent. Prefer semantic Tailwind tokens over raw gray/white classes.
- Keep components small and focused. Avoid mixing fetching, orchestration, layout, and presentation in one large file.
- Remove dead or duplicate frontend code during frontend changes.

## Commands

Full local validation:

```bash
./scripts/validate.sh
```

Backend tests:

```bash
cd backend
../backend/.venv/bin/python -m unittest discover -s tests
```

Eval fixture tests:

```bash
cd backend
../backend/.venv/bin/python -m unittest tests.test_eval_fixtures -v
```

Python compile check:

```bash
backend/.venv/bin/python -m compileall backend -q
```

FastAPI import and OpenAPI generation:

```bash
cd backend
../backend/.venv/bin/python -c "from main import app; schema=app.openapi(); print(app.title); print(sorted(schema.get('components', {}).get('schemas', {}).keys()))"
```

Run migrations from the host against the Compose-mapped database:

```bash
cd backend
DATABASE_URL='postgresql+psycopg://<user>:<password>@localhost:5433/prompt_builder' ../backend/.venv/bin/alembic upgrade head
```

Check current DB revision:

```bash
cd backend
DATABASE_URL='postgresql+psycopg://<user>:<password>@localhost:5433/prompt_builder' ../backend/.venv/bin/alembic current
```

Run frontend locally:

```bash
cd frontend
npm install
npm run dev
```

Build frontend:

```bash
cd frontend
npm run build
```

## Verification Checklist

For backend schema, prompt, OpenAI, migration, or persistence changes:

- Run `./scripts/validate.sh`.
- Check generated OpenAI JSON schema.
- Check FastAPI OpenAPI generation.
- Run Alembic `heads`; run `current` when a live DB is available.
- Verify DB constraints when migrations change.

For frontend auth, routing, API client, or workspace changes:

- Run `npm run build`.
- Check login and register routes.
- Check mobile and desktop layouts.
- Check browser console errors.
- Confirm unauthenticated users do not call conversation endpoints.
- Confirm authenticated users can load the workspace.
- Remove dead components, hooks, imports, and duplicate implementations.

## Tests And Evals

- Route-level `/chat` tests live in `backend/tests/test_chat_endpoint.py`.
- These tests mock auth and agent/OpenAI boundaries, spend zero OpenAI tokens, and assert both response shape and persisted DB state.
- They cover conversation creation, ask-question flow, final-prompt flow, persisted state/messages/final prompts, rate limiting, read endpoints, ownership protection, and UUID validation.
- `/chat` tests parse SSE and use the final done event because safe `status` events can appear first.
- `FakeAgent` must implement `stream_run()` as an async generator alongside `run()`.
- Offline eval fixtures live in `backend/evals/fixtures/agent_behavior_scenarios.json`.
- Eval checks live in `backend/evals/agent_behavior.py` and `backend/tests/test_eval_fixtures.py`.

## Local Gotchas

- `backend/.env` may use `postgres` as DB host. That works inside Docker Compose, not from the host shell. Use `localhost:5433` from the host.
- Docker socket access may be blocked in the agent shell.
- Google OAuth requires real Google Cloud OAuth credentials. Placeholder values are rejected before redirecting to Google.
- `backend/venv/`, `backend/.venv/`, and migration `__pycache__` are ignored.
- Frontend dependencies target Node `>=18.19.0` and Vite `6.4.2` or newer in the Vite 6 line.
- Message ordering should not rely only on Postgres `now()` timestamps inside the same transaction. `memory.add_message()` sets Python UTC timestamps for stable ordering.

## Possible Improvements

Agent quality:

- Add prompt refinement mode so users can revise an existing `final_prompt` with requests such as shorter, more formal, more detailed, or with examples.
- Add prompt export formats alongside XML: plain text, markdown, and JSON-keyed fields.
- Generate concise conversation titles on the first user message using the existing agent turn when possible, or a cheap separate model call if justified.
- Add conversation summarization for long threads before older messages fall out of `MAX_HISTORY_CHARS`.
- Consider smarter model routing: a cheaper/faster model for `ask_question` turns and a stronger model for `final_prompt` generation.
- Implement true streaming through incremental JSON parsing only if the one-call-per-turn rule and final schema validation can be preserved.

Product and frontend:

- Add frontend contract documentation for auth, SSE events, conversation state, read endpoints, and final prompt responses.
- Improve final prompt UX with version history, copy actions per export format, and clearer revision entry points.
- Add empty, loading, error, and offline states for every conversation workflow that can fail.
- Add Playwright coverage for login/register routes, auth-gated workspace behavior, start-page submission, conversation loading, and final prompt display.
- Add accessibility checks for keyboard navigation, focus states, color contrast, and screen-reader labels.

Reliability and operations:

- Add `/health` and `/ready` endpoints. `/ready` should check DB connectivity and required config without exposing secrets.
- Add a JWT refresh or sliding-session strategy before production.
- Add production config checks for secure cookies, strong secrets, CORS origins, and OAuth placeholders.
- Add structured request IDs across backend logs and frontend error reporting while keeping logs privacy-safe.
- Add migration drift checks in CI: Alembic heads, current revision against a test DB, and schema constraints.

Evaluation and testing:

- Expand evals from static fixtures toward captured or mocked multi-turn conversations.
- Add regression tests for prompt refinement and final prompt versioning when those features are implemented.
- Add performance budgets for frontend bundle size and backend `/chat` non-LLM overhead.
- Add load tests for rate limiting and conversation read endpoints without calling OpenAI.
