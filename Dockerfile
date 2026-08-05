# LINKAVTO — образ витрины для платформы awwwdde (система под-сайтов).
#
# Контракт гостя (back/engine.py платформы):
#   • Dockerfile в корне репозитория, build context = корень;
#   • приложение слушает порт 8080 внутри контейнера;
#   • GET /healthz отвечает 200, когда сервис готов — панель ждёт его
#     изнутри контейнера (`wget -qO- localhost:8080/healthz`) до 120 с,
#     и только после этого прописывает маршрут в Caddy;
#   • БД берётся из DATABASE_URL, миграции/seed — на старте контейнера.
#
# Последний пункт здесь не используется намеренно: витрина — статический SPA
# на MSW-моках (VITE_ENABLE_MOCKS=true в frontend/.env.production), реального
# /api/v1/ пока нет. Парный <slug>_db, который панель поднимает каждому гостю,
# просто простаивает. Старый Django (backend/) в образ не входит — он отдаёт
# другой контракт (/api/ на 8 эндпоинтов), новой витрине он не подходит.
#
# Панель прокидывает в контейнер DATABASE_URL / PUBLIC_SITE_URL / SECRET_KEY /
# JWT_SECRET и пользовательские env-vars. Статическая сборка их прочитать не
# может — всё, что нужно фронту, вшивается на этапе build из .env.production.

# ─── Stage 1: сборка SPA ───────────────────────────────────────────────────
# node:20-slim (glibc), а НЕ alpine (musl): у Tailwind v4 (@tailwindcss/oxide)
# и lightningcss нативные бинарники — под glibc prebuilt-сборки надёжнее, иначе
# `vite build` падает в контейнере.
FROM node:20-slim AS web
WORKDIR /build/frontend

RUN corepack enable && corepack prepare pnpm@9.12.0 --activate

# Манифест и лок — отдельным слоём: пока зависимости не менялись, пересборка
# после правки исходников не тянет установку заново (на 2 vCPU это минуты).
COPY frontend/package.json frontend/pnpm-lock.yaml ./
# node_modules НЕ копируется (см. .dockerignore) — ставим свежие бинарники под linux.
RUN pnpm install --frozen-lockfile

COPY frontend ./
# vite build читает .env.production (VITE_ENABLE_MOCKS=true). tsc-проверка уже
# прогнана в разработке — в образе делаем только сборку бандла.
RUN pnpm exec vite build

# ─── Stage 2: раздача статики nginx ────────────────────────────────────────
FROM nginx:1.27-alpine
COPY frontend/deploy/nginx.conf /etc/nginx/nginx.conf
COPY --from=web /build/frontend/dist /srv/web

EXPOSE 8080
# Дублирует healthcheck панели — чтобы `docker ps` тоже показывал состояние.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:8080/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
