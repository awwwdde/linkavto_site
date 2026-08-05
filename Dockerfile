# LINKAVTO — образ витрины для платформы awwwdde.
#
# Контракт панели:
#   • один контейнер, слушает порт 8080 внутри;
#   • GET /healthz → 200, когда сервис готов;
#   • Dockerfile в корне репозитория (build context = корень).
#
# Демо-режим: данные отдаёт MSW прямо в браузере (VITE_ENABLE_MOCKS=true в
# frontend/.env.production), поэтому бэкенд и Postgres не используются —
# парный postgres-контейнер от панели просто игнорируется.

# ─── Stage 1: сборка SPA ───────────────────────────────────────────────────
# node:20-slim (glibc), а НЕ alpine (musl): у Tailwind v4 (@tailwindcss/oxide)
# и lightningcss нативные бинарники — под glibc prebuilt-сборки надёжнее, иначе
# `vite build` падает в контейнере.
FROM node:20-slim AS web
WORKDIR /build

RUN corepack enable && corepack prepare pnpm@9.12.0 --activate

# node_modules НЕ копируется (см. .dockerignore) — ставим свежие бинарники под linux.
COPY frontend ./frontend
WORKDIR /build/frontend

RUN pnpm install --no-frozen-lockfile
# vite build читает .env.production (VITE_ENABLE_MOCKS=true). tsc-проверка уже
# прогнана в разработке — в образе делаем только сборку бандла.
RUN pnpm exec vite build

# ─── Stage 2: раздача статики nginx ────────────────────────────────────────
FROM nginx:1.27-alpine
COPY frontend/deploy/nginx.conf /etc/nginx/nginx.conf
COPY --from=web /build/frontend/dist /srv/web
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
