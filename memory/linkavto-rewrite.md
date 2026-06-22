---
name: linkavto-rewrite
description: Проект linkavto — перенос Django-магазина на React/TS/Tailwind/Zustand (актуально: ветка docker)
metadata:
  type: project
---

Проект `linkavto` — большой Django 5.1 маркетплейс автозапчастей. Задача: воспроизвести **ВЕСЬ** сайт на **React + TypeScript + Tailwind + Zustand**, строго **pixel-perfect**, плюс отполировать плавность/анимации через **GSAP + Framer Motion + Lenis** («прилизать до идеала»). Приоритет — фронтенд; бэкендеры доделают API сами.

**АКТУАЛЬНАЯ КОДОВАЯ БАЗА — ветка `docker`** из `https://gitlab.com/ilyafeoktistov005/linkavto.git` (репо публичное, https-clone без авторизации; ssh-ключ не подходит). Склонирована в `linkavto-docker/`. Старые папки `backend/` и `frontend/` в корне — от ПЕРВОЙ (неверной) попытки на устаревшем коде, их игнорировать/не использовать.

**Эталон pixel-perfect** = сам Django-сайт docker-ветки, запущенный локально на :8000.

Запуск backend (docker-ветка, БЕЗ Docker, на SQLite):
- venv: `linkavto-docker/.venv`, зависимости из requirements.txt (psycopg2-binary 2.9.12 ставится под py3.13).
- `.env` создан: `DATABASE=sqlite`, `ENABLE_CAPTCHA=0`, console email, заглушки ключей.
- В `avtolink/settings/development.py` добавлен override: при `DATABASE=sqlite` в .env используется SQLite (дефолт остаётся postgres — прод не тронут). settings/__init__.py по умолчанию грузит development.
- `python manage.py migrate`; данные генерируются командами: `fill_catalog` (49 категорий: корневые Легковые/Грузовые/Мото/Спец/Шины/Для ТО + части), `fill_car_brands` (136 марок), `load_test_data` (товары). ВАЖНО: fill_* печатают «✓» — на Windows нужен `PYTHONUTF8=1`/`PYTHONIOENCODING=utf-8`, иначе UnicodeEncodeError (данные при этом могут записаться частично). `fill_car_models` пропускаем (стучится в NHTSA API, долго).
- Запуск: `python manage.py runserver 127.0.0.1:8000` (логам тоже нужен PYTHONUTF8=1). Категории без картинок → штатный градиентный фолбэк (фото на проде заливали вручную, это косметика).
- DRF в INSTALLED_APPS закомментирован → нужно добавить минимальный API для React (как раньше делали в `api/` приложении).

`.claude/launch.json`: configs `backend` (docker-ветка manage.py :8000) и `frontend` (npm dev :5173, cwd). Превью: vite ДОЛЖЕН слушать IPv4 — `server.host:true` в vite.config (иначе [::1] и 127.0.0.1 не коннектится).

МЕТОДОЛОГИЯ pixel-perfect (обязательна): НЕ approximate. Для каждого блока читать точную разметку и CSS из `linkavto-docker/shop/templates/shop/base.html` (шапка: строки ~3042-3273; CSS шапки ~119-420) и соответствующих шаблонов, переносить значения 1:1. Сверять скриншот React (:5173) с эталоном Django (:8000) при одинаковой ширине.

СТРУКТУРА ШАПКИ (важно, проверено замером прода): синяя плашка `header.sticky-top` НЕ полноширинная — `max-width:1520px; margin:auto; height:80px; border-radius:0 0 10px 10px; background:#A7D2EF` → центрирована, по бокам БЕЛЫЕ поля. Строка «Указать адрес/Стать продавцом» (`.product-nav`, пункты h40 px16 bg#F3F4F6 r10 текст15/#272526) — ВНЕ синей плашки, НИЖЕ, на белом, справа. (Обёртки `.header-wrapper`/`.header-inner` max-w-1520 центрируют оба.) Частая ошибка: НЕ делать синий на всю ширину и НЕ вкладывать product-nav внутрь синего.

Прогресс фронта (linkavto-docker/frontend): Header переписан ТОЧНО (готов) — иконки .Header-icons-right #7BAACF 60×60 radius12 со стрелк. SVG #2E2E2E (Гараж/Избранное/Корзина/Профиль, inline Lucide); кнопка «Каталог» #7BAACF h60 px24 r15 шрифт16; поиск #F3F4F6 без рамки r12 h50 иконка слева 15px placeholder #95a5a6; контейнер max-w-1520 px-5 py-2.5; вторая панель product-nav (h40 px16 bg#F3F4F6 r10 текст15/#272526) «Указать адрес»+«Стать продавцом» справа. Lenis-скролл в App. ОСТАЛОСЬ переписать ТОЧНО (старые компоненты — приблизительные, переделать): HeroCarousel, CategoryGrid, мега-меню каталога, Catalog (с сайдбаром фильтров — пользователь жаловался что каталог не похож), ProductCard/Compact, Product, Cart, Checkout + страницы garage/sellers/account/search и т.д. (всего ~30 типов).

Дизайн-токены с оригинала: шапка `#A7D2EF`; кнопка «Каталог»/иконки `#7BAACF` (radius 12px, БЕЗ рамки); акцент/цена `#89BEE8`; поиск — рамка `#dee2e6` (НЕ чёрная); градиент категорий 135° `#667eea→#764ba2` radius 15px; контейнер max-width **1520px** px-4; шапка sticky. Кнопка «Каталог» открывает выпадающее меню категорий; в шапке также «Указать адрес» и «Стать продавцом». Шрифт Inter.
