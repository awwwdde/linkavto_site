# LINKAVTO

Маркетплейс автозапчастей. Репозиторий — монорепо из двух независимых частей.

```
.
├── frontend/     SPA-витрина (React 19 + TS + Vite) — актуальная разработка
├── backend/      Django-приложение старого сайта (legacy, API ещё не переписан)
├── Dockerfile    сборка образа витрины (build context = корень)
└── .dockerignore в образ попадает только frontend/
```

## Правила раскладки

- Всё, что относится к витрине, живёт **только** в `frontend/` (исходники, публичные
  ассеты, конфиг nginx в `frontend/deploy/`, `.env.production`).
- Всё, что относится к Django, живёт **только** в `backend/` (приложения, шаблоны
  внутри `backend/<app>/templates/<app>/`, статика в `backend/static/`, деплой-скрипты
  в `backend/deploy/`, документация в `backend/docs/`).
- В корне лежит исключительно инфраструктура сборки всего репозитория.
- Дампы БД, бэкапы, `staticfiles/`, история шелла, pid-файлы и прочие артефакты
  рантайма в репозиторий не коммитятся — см. `.gitignore`.

## frontend

```bash
cd frontend && pnpm install && pnpm dev
```

Витрина работает на MSW-моках `/api/v1/` — реальный бэкенд для разработки не нужен.
Подробности: [frontend/projectoverview.md](frontend/projectoverview.md),
контракт API — [frontend/API_REQUESTS.md](frontend/API_REQUESTS.md).

Прод-образ: `docker build -t linkavto .` — многостадийная сборка Vite → nginx,
слушает `:8080`, healthcheck на `GET /healthz`.

## backend

Django 5.1, настройки — `avtolink.settings`.

```bash
cd backend && pip install -r requirements.txt && python manage.py runserver
```

Legacy: старый сайт целиком (каталог, корзина, заказы, продавцы, гараж, поиск).
Новая витрина на него пока не ходит — переезд на `/api/v1/` запланирован отдельно.
Документация по БД и деплою — в [backend/docs/](backend/docs/).
