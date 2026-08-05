# Демо-стенд витрины LINKAVTO на MSW-моках (бэкенд не требуется).
# Сборка фронта → отдача статики nginx на порту 8080 (как agregator).

# ── 1. Сборка ────────────────────────────────────────────────────────────
FROM node:22-alpine AS build
WORKDIR /app

# Ставим зависимости отдельным слоем для кэша.
COPY package.json pnpm-lock.yaml* ./
RUN corepack enable && pnpm install --prod=false

COPY . .
# .env.production включает VITE_ENABLE_MOCKS=true — витрина работает на моках.
RUN pnpm run build

# ── 2. Отдача статики ────────────────────────────────────────────────────
FROM nginx:1.27-alpine
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /srv/web
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
