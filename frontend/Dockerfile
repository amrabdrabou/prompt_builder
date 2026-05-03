# ── Stage 1: install dependencies ───────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# ── Stage 2: local dev server (used by docker compose) ──────────────────────
FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ── Stage 3: production build ────────────────────────────────────────────────
FROM deps AS builder
COPY . .
RUN npm run build

# ── Stage 4: production nginx serve ─────────────────────────────────────────
FROM nginx:alpine AS prod
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
