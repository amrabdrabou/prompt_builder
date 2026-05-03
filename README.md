# Prompt Builder

Prompt Builder is an agent-powered workspace for turning rough ideas into precise, reusable prompts.

Instead of trying to answer your original request directly, the agent behaves like a careful prompt architect: it listens, asks focused clarifying questions, tracks what is known, notices what is still missing, and finally returns a reviewed XML prompt that is ready to use with another AI system.

It is built for the messy middle of prompt creation, where you know what you want but not yet how to say it cleanly.

## How The Agent Works

The agent follows a structured conversation loop:

1. Understand the rough prompt.
2. Extract the goal, audience, constraints, and output format.
3. Maintain structured conversation state.
4. Ask the next best question when important details are missing.
5. Generate a final XML prompt only when the request is clear enough.
6. Review the final prompt for clarity, valid XML, missing details, and quality.

The final result is not just a chat response. It is a validated prompt artifact with a `<prompt>` root and required sections for role, goal, context, instructions, constraints, and output format.

## Screenshots

### Login
![Login page](docs/screenshots/login.png)

### Start Page
![Start page — choose prompt type and describe your goal](docs/screenshots/start.png)

### Conversation
![Agent asks clarifying questions and tracks state](docs/screenshots/conversation.png)

### Final Prompt
![Generated XML prompt with quality review](docs/screenshots/final-prompt.png)

---

## What You Need

Install these first:

- Docker Desktop
- A Google account
- An OpenAI API key

You do not need to install Python, Node, PostgreSQL, or any developer tools if you run the app with Docker.

---

## Setup

### 1. Create the project `.env` file

In the main project folder, create a file named `.env` (copy from `.env.example`):

```bash
cp .env.example .env
```

Then open `.env` and set a password:

```env
POSTGRES_USER=prompt_builder
POSTGRES_PASSWORD=replace_with_a_password
POSTGRES_DB=prompt_builder
```

### 2. Create the backend `.env` file

In the `backend` folder, create a file named `.env`:

```env
DATABASE_URL=postgresql+psycopg://prompt_builder:replace_with_a_password@postgres:5432/prompt_builder
OPENAI_API_KEY=replace_with_your_openai_api_key

LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3
SQL_ECHO=false
LOG_LEVEL=INFO

GOOGLE_CLIENT_ID=replace_with_your_google_client_id
GOOGLE_CLIENT_SECRET=replace_with_your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

JWT_SECRET_KEY=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

FRONTEND_URL=http://localhost:5173
GOOGLE_SERVER_METADATA_URL=https://accounts.google.com/.well-known/openid-configuration

SESSION_SECRET_KEY=replace_with_a_second_long_random_secret

AUTH_COOKIE_NAME=access_token
AUTH_COOKIE_SECURE=false
AUTH_COOKIE_SAMESITE=lax
```

The database password in `DATABASE_URL` must match the password in the root `.env` file.

### 3. Get Google login credentials

The app uses Google OAuth. You need to create a Google OAuth client.

1. Open [Google Cloud Console](https://console.cloud.google.com).
2. Create or choose a project.
3. Go to **APIs & Services → OAuth consent screen** and finish the setup.
4. Go to **Credentials → Create credentials → OAuth client ID**.
5. Choose **Web application**.
6. Add this Authorized redirect URI:

```
http://localhost:8000/auth/google/callback
```

7. Copy the Client ID into `GOOGLE_CLIENT_ID`.
8. Copy the Client Secret into `GOOGLE_CLIENT_SECRET`.

### 4. Get an OpenAI API key

Create an API key from your [OpenAI account](https://platform.openai.com/api-keys) and paste it into:

```env
OPENAI_API_KEY=replace_with_your_openai_api_key
```

Keep this key private. Never commit it to git.

### 5. Generate random secrets

The app needs two long random secret values:

```bash
openssl rand -hex 32   # paste into JWT_SECRET_KEY
openssl rand -hex 32   # paste into SESSION_SECRET_KEY
```

---

## Running the App

### Start (all three services)

```bash
docker compose --profile frontend up --build
```

The backend automatically runs database migrations on every startup — no manual migration step is needed.

The frontend container is attached to the `frontend` Docker Compose profile. That means it starts only when you include `--profile frontend`.

Once running, open:

| Service  | URL                       |
|----------|---------------------------|
| Frontend | http://localhost:5173      |
| Backend  | http://localhost:8000      |

### Start (backend + database only, no frontend container)

```bash
docker compose up --build
```

This starts the default Compose services only:

- PostgreSQL
- FastAPI backend

Use this when running the frontend locally with `npm run dev` or deploying it separately, for example to Vercel. This is the fastest local development path when you want Vite hot reload outside Docker.

### Start the frontend locally without the frontend container

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:5173
```

### Stop

```bash
# Ctrl+C in the running terminal, then:
docker compose --profile frontend down
```

---

## Deploying to Production

### Backend (self-hosted with Docker)

The backend `Dockerfile` has a production-ready stage. Set `AUTH_COOKIE_SECURE=true` and use HTTPS.

### Frontend (self-hosted with nginx)

```bash
docker build --target prod -t prompt-builder-frontend ./frontend
docker run -p 80:80 prompt-builder-frontend
```

### Frontend (Vercel)

Set the `VITE_API_BASE_URL` environment variable to your backend URL in the Vercel project settings, then connect the `frontend/` directory as the root.

---

## Troubleshooting

### Google says `invalid_client`

Your OAuth values are wrong or still contain placeholders. Check `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in `backend/.env`, and confirm the redirect URI is set in Google Cloud Console.

After fixing, restart the backend:

```bash
docker compose up -d --force-recreate backend
```

### The page cannot connect to the backend

Make sure Docker is running, then check:

```bash
docker compose ps
```

The backend should be on port `8000`. You can also open `http://localhost:8000` — it should say the backend is running.

### Login works but the agent does not respond

Check that `OPENAI_API_KEY` is set correctly in `backend/.env`, then restart:

```bash
docker compose up -d --force-recreate backend
```

### Database migration error on startup

The backend runs `alembic upgrade head` automatically. If it fails, check that:

- The `DATABASE_URL` password matches `POSTGRES_PASSWORD` in the root `.env`.
- The `postgres` container is healthy before the backend starts (`docker compose ps`).

To run migrations manually:

```bash
docker compose exec backend alembic upgrade head
```

---

## Security Notes

- Do not share or commit `.env` files.
- If an API key was accidentally exposed, revoke it immediately and create a new one.
- `AUTH_COOKIE_SECURE=false` is only for local HTTP. Set it to `true` in production behind HTTPS.
- JWT tokens expire after 24 hours by default (`JWT_EXPIRE_MINUTES=1440`).
