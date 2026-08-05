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

## Деплой как под-сайт awwwdde

Репозиторий соответствует контракту гостя платформы
[awwwdde](https://github.com/awwwdde/vlad) (`back/engine.py`):

| Требование платформы | Как выполнено |
|---|---|
| `Dockerfile` в корне, build context = корень | [Dockerfile](Dockerfile), в контекст едет только `frontend/` (см. [.dockerignore](.dockerignore)) |
| приложение слушает `:8080` | nginx `listen 8080` — [frontend/deploy/nginx.conf](frontend/deploy/nginx.conf) |
| `GET /healthz` → `200`, когда готов | отдаёт nginx; панель ждёт его изнутри контейнера до 120 с и только потом прописывает маршрут в Caddy |
| БД из `DATABASE_URL`, миграции на старте | **не используется** — витрина статическая, на MSW-моках |

Панель поднимает гостю пару контейнеров `linkavto_app` + `linkavto_db` в сети
`awwwdde_net` и вешает маршрут `linkavto.awwwdde.art → linkavto_app:8080`.
Postgres при этом простаивает: реального `/api/v1/` пока нет, данные отдаёт
Mock Service Worker прямо в браузере. Старый Django в образ не входит намеренно
— он реализует другой контракт (`/api/`, 8 эндпоинтов), новой витрине он не
подходит.

Панель прокидывает в контейнер `DATABASE_URL`, `PUBLIC_SITE_URL`, `SECRET_KEY`,
`JWT_SECRET` и пользовательские env-vars. Статическая сборка читать их не может:
всё, что нужно фронту, вшивается на этапе `vite build` из
[frontend/.env.production](frontend/.env.production).

### Как развернуть

1. Запушить ветку в GitHub (панель клонирует репозиторий `--depth 1`; если репо
   приватный, на VPS нужен deploy-ключ).
2. В админке `https://awwwdde.art/admin/projects` → «+ Новый»:
   - **slug**: `linkavto` — из него собираются и поддомен, и имена контейнеров;
   - **source**: `https://github.com/awwwdde/linkavto_site.git`;
   - галка «развернуть сразу».
3. Через ~3–7 минут (build + healthcheck) открывается `https://linkavto.awwwdde.art`.

Свой домен (например `linkavto.ru`) добавляется в карточке проекта — Caddy
выпустит ему TLS, как только A-запись укажет на сервер. Фронт к хосту не
привязан (`server_name _`, все запросы относительные), так что менять ничего
не нужно.

Ошибка деплоя видна в карточке проекта (`last_error`) и в кнопке «Логи»
(`docker logs linkavto_app` — nginx пишет в stdout/stderr).

## backend

Django 5.1, настройки — `avtolink.settings`.

```bash
cd backend && pip install -r requirements.txt && python manage.py runserver
```

Legacy: старый сайт целиком (каталог, корзина, заказы, продавцы, гараж, поиск).
Новая витрина на него пока не ходит — переезд на `/api/v1/` запланирован отдельно.
Документация по БД и деплою — в [backend/docs/](backend/docs/).
