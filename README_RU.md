# Сервис Заметок Markdown (Markdown Note Service)

[![CI](https://github.com/CHUKEPC/markdown-notes/actions/workflows/ci.yml/badge.svg)](https://github.com/CHUKEPC/markdown-notes/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5](https://img.shields.io/badge/Django-5.0+-092e20.svg?style=flat&logo=Django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.15+-red.svg)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1.svg?style=flat&logo=PostgreSQL&logoColor=white)](https://www.postgresql.org/)
[![Bleach](https://img.shields.io/badge/Bleach-6.1+-orange.svg)](https://github.com/mozilla/bleach)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Надёжный, готовый к production бэкенд для ведения заметок и базы знаний в формате Markdown, построенный на **Django 5**, **Django REST Framework** и **PostgreSQL**. Включает серверный рендеринг Markdown в HTML с санитизацией против XSS через **Bleach**, полнотекстовый поиск PostgreSQL на базе `tsvector`/`tsquery`, версионирование заметок с историей unified diff и откатом к любой версии, публичный шаринг по секретной ссылке с опциональным сроком жизни, таксономию категорий и тегов, импорт/экспорт (JSON, Markdown, ZIP архивы) и токен-аутентификацию.

---

## Возможности

- **Серверный конвейер Markdown → HTML**: Преобразование исходного Markdown в валидный HTML с поддержкой таблиц, блоков кода с подсветкой, списков и цитат. Очистка через Bleach гарантирует защиту от межсайтового скриптинга (XSS).
- **Полнотекстовый поиск (FTS)**: Высокопроизводительный поиск PostgreSQL с использованием весовых векторов `SearchVector` (заголовок взвешивается выше тела) и ранжирования `SearchRank`, с прозрачным фоллбэком на SQLite для локального тестирования.
- **Версионирование и история правок**: Каждое обновление заметки фиксирует снимок: последовательный номер версии, временную метку, описание изменений и unified diff относительно прошлой версии. Доступен откат к любой версии в один запрос.
- **Публичный шаринг по ссылке**: Генерация криптографически стойких токенов (64 символа) с опциональным сроком жизни (от 1 до 365 дней). Публичный просмотр без необходимости авторизации.
- **Категории и теги**: Группировка заметок по категориям с собственными цветами и slug, а также гибкие сквозные Many-to-Many теги.
- **Избранное и закрепление**: Закрепление приоритетных заметок в топе списка и фильтрация по признаку избранного.
- **Импорт и экспорт**:
  - Экспорт отдельной заметки в Markdown с YAML-метаданными (frontmatter) или в формате JSON.
  - Экспорт всей коллекции заметок пользователя в виде скачиваемого `.zip` архива.
  - Импорт заметок из загружаемых Markdown файлов (с парсингом заголовка, тегов и категории из frontmatter) или пакетом через JSON.
- **Фильтрация и пагинация**: Гибкая фильтрация по тегам, категориям, датам создания/обновления и флагам через `django-filter`. Поддержка стандартной и курсорной (cursor-based) пагинации.
- **Аутентификация по токенам**: Регистрация, логин, логаут и профиль пользователя с токенами DRF TokenAuth (`Token <key>`).
- **Строгая изоляция данных**: Разграничение прав на уровне объектов (object-level permissions), исключающее доступ к чужим данным.

---

## Технологический стек

| Компонент | Технология | Назначение |
|---|---|---|
| **Веб-фреймворк** | Django 5.2+ | Основной каркас веб-приложения |
| **REST API** | Django REST Framework 3.18+ | Реализация REST API, сериализаторы, viewsets |
| **База данных** | PostgreSQL 16+ | Реляционное хранилище с полнотекстовым поиском |
| **Рендерер Markdown** | Python Markdown | Парсинг и генерация HTML из Markdown |
| **Санитизация** | Bleach 6.4+ | Очистка HTML по белому списку тегов и атрибутов |
| **Фильтрация** | django-filter 26+ | Фильтрация QuerySet по параметрам запроса |
| **Типизация и линтинг** | Mypy (strict mode) & Ruff | Статический анализ типов со stubs и быстрый линтинг |
| **Тестирование** | pytest, pytest-django, pytest-cov | 50 тестов с покрытием кода **92%** |
| **Контейнеризация** | Docker & Docker Compose | Многоэтапный Dockerfile и оркестрация стека |

---

## Архитектура и структура проекта

Проект спроектирован по принципам чистой архитектуры в рамках модульного Django layout. Бизнес-логика вынесена в слой `services/`, рендеринг — в `renderers.py`, версионирование — в `versioning.py`, поиск — в `search.py`.

```
markdown-notes/
├── src/
│   ├── manage.py                     # Корневой скрипт управления Django
│   └── markdown_notes/
│       ├── __init__.py
│       ├── manage.py                 # Скрипт manage.py внутри пакета
│       ├── config/                   # Конфигурация проекта
│       │   ├── __init__.py
│       │   ├── settings.py           # Настройки БД, DRF, приложений
│       │   ├── urls.py               # Корневая маршрутизация
│       │   └── wsgi.py               # WSGI-обработчик
│       ├── notes/                    # Основное приложение заметок
│       │   ├── __init__.py
│       │   ├── apps.py
│       │   ├── models.py             # Модели Note, Category, Tag, NoteVersion
│       │   ├── serializers.py        # Сериализаторы DRF
│       │   ├── views.py              # ViewSets и контроллеры API
│       │   ├── urls.py               # Роутинг заметок, тегов, категорий
│       │   ├── filters.py            # Наборы фильтров django-filter
│       │   ├── services.py           # Бизнес-слой NoteService
│       │   ├── search.py             # Логика полнотекстового поиска
│       │   ├── versioning.py         # Создание снимков и вычисление diff
│       │   ├── renderers.py          # Markdown рендеринг и Bleach санитизация
│       │   └── permissions.py        # IsOwner и IsOwnerOrSharedReadOnly
│       ├── users/                    # Приложение аутентификации
│       │   ├── __init__.py
│       │   ├── apps.py
│       │   ├── models.py             # Кастомная модель User
│       │   ├── serializers.py        # Сериализаторы регистрации и профиля
│       │   ├── views.py              # Регистрация, логин, логаут, me
│       │   └── urls.py               # Маршруты авторизации
│       └── utils/                    # Вспомогательные компоненты
│           ├── __init__.py
│           ├── apps.py
│           └── pagination.py         # Классы пагинации
├── tests/                            # Набор автоматизированных тестов (50 тестов)
│   ├── conftest.py                   # Фикстуры клиентов и моделей
│   ├── test_notes/
│   │   ├── test_models.py
│   │   ├── test_views.py
│   │   ├── test_services.py
│   │   ├── test_renderers.py
│   │   ├── test_versioning.py
│   │   ├── test_search.py
│   │   ├── test_sharing.py
│   │   └── test_permissions.py
│   ├── test_users/
│   │   ├── test_models.py
│   │   └── test_views.py
│   └── test_utils/
│       └── test_pagination.py
├── docker-compose.yml                # Оркестрация контейнеров
├── Dockerfile                        # Многоэтапная сборка образа
├── Makefile                          # Команды автоматизации
├── pyproject.toml                    # Зависимости и конфигурации инструментов
├── .env.example                      # Шаблон переменных окружения
├── README.md                         # Документация на английском
└── README_RU.md                      # Документация на русском
```

---

## Быстрый старт

### Требования
- Python 3.11+
- PostgreSQL 16+ (или Docker)

### Вариант 1: Запуск через Docker Compose (Рекомендуется)

1. **Клонирование репозитория**:
   ```bash
   git clone https://github.com/CHUKEPC/markdown-notes.git
   cd markdown-notes
   ```

2. **Запуск сервисов**:
   ```bash
   docker compose up -d --build
   ```

3. **Проверка работоспособности**:
   ```bash
   curl http://localhost:8000/api/health/
   ```

---

### Вариант 2: Локальная установка в виртуальное окружение

1. **Создание и активация виртуального окружения**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Установка зависимостей**:
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -e ".[dev]"
   ```

3. **Настройка переменных окружения**:
   ```bash
   cp .env.example .env
   # Укажите параметры PostgreSQL или оставьте по умолчанию для запуска с SQLite
   ```

4. **Применение миграций**:
   ```bash
   python src/markdown_notes/manage.py migrate
   ```

5. **Запуск сервера разработки**:
   ```bash
   python src/markdown_notes/manage.py runserver 0.0.0.0:8000
   ```

---

## Справочник REST API

Все защищённые эндпоинты требуют заголовок авторизации:
```http
Authorization: Token <ваш_токен>
```

### 1. Аутентификация и профиль (`/api/users/`)

| Метод | Эндпоинт | Описание | Авторизация |
|---|---|---|---|
| `POST` | `/api/users/register/` | Регистрация нового пользователя с выдачей токена | Нет |
| `POST` | `/api/users/login/` | Авторизация по логину и паролю | Нет |
| `POST` | `/api/users/logout/` | Завершение сессии и удаление токена | Да |
| `GET` | `/api/users/me/` | Получение профиля текущего пользователя | Да |
| `PATCH` | `/api/users/me/` | Обновление данных профиля | Да |

#### Пример регистрации
```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "developer",
    "email": "dev@example.com",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "bio": "Python Backend Developer"
  }'
```

---

### 2. Заметки (CRUD и действия) (`/api/notes/`)

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/notes/` | Список заметок с фильтрацией, поиском и пагинацией |
| `POST` | `/api/notes/` | Создание заметки (рендеринг HTML и создание версии 1) |
| `GET` | `/api/notes/{id}/` | Полные данные заметки с отрендеренным HTML |
| `PUT` | `/api/notes/{id}/` | Обновление заметки (создание новой версии с diff) |
| `DELETE` | `/api/notes/{id}/` | Удаление заметки |
| `POST` | `/api/notes/{id}/pin/` | Закрепить / открепить заметку |
| `POST` | `/api/notes/{id}/favorite/` | Добавить / удалить из избранного |
| `POST` | `/api/notes/{id}/share/` | Создать публичную ссылку с опциональным сроком |
| `POST` | `/api/notes/{id}/revoke-share/` | Отозвать публичную ссылку |
| `GET` | `/api/notes/{id}/versions/` | История версий заметки |
| `GET` | `/api/notes/{id}/versions/{v}/` | Получение конкретной версии |
| `POST` | `/api/notes/{id}/versions/{v}/revert/` | Откат заметки к указанной версии |
| `GET` | `/api/notes/{id}/versions/{v1}/diff/?compare_to={v2}` | Diff между версиями |
| `GET` | `/api/notes/{id}/export/?export_format=markdown` | Экспорт заметки в Markdown с frontmatter |
| `GET` | `/api/notes/{id}/export/?export_format=json` | Экспорт заметки в JSON |
| `GET` | `/api/notes/export-all/` | Скачивание всех заметок в ZIP-архиве |
| `POST` | `/api/notes/import/` | Импорт из файла `.md` или массива JSON |
| `GET` | `/api/notes/shared/{share_token}/` | **Публичный эндпоинт** просмотра расшаренной заметки |

#### Пример создания заметки
```bash
curl -X POST http://localhost:8000/api/notes/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Архитектура Django REST Framework",
    "content": "# Архитектура\n\n- Модели\n- Сериализаторы\n- Сервисный слой\n\n```python\nprint(\"Clean Code\")\n```",
    "category_id": 1,
    "tags": ["Django", "Python"],
    "is_pinned": true
  }'
```

#### Пример публичного шаринга
```bash
# Создание ссылки с экспирацией через 7 дней
curl -X POST http://localhost:8000/api/notes/<note_id>/share/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"expires_in_days": 7}'

# Просмотр без авторизации
curl http://localhost:8000/api/notes/shared/<share_token>/
```

---

### 3. Категории и теги (`/api/categories/`, `/api/tags/`)

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/categories/` | Список категорий с подсчётом заметок |
| `POST` | `/api/categories/` | Создание категории (автогенерация slug) |
| `GET` | `/api/categories/{id}/` | Просмотр категории |
| `PUT` | `/api/categories/{id}/` | Обновление названия, цвета, описания |
| `DELETE` | `/api/categories/{id}/` | Удаление категории |
| `GET` | `/api/tags/` | Список тегов с подсчётом заметок |
| `POST` | `/api/tags/` | Создание тега |
| `DELETE` | `/api/tags/{id}/` | Удаление тега |

---

### 4. Полнотекстовый поиск и фильтрация

```bash
# Полнотекстовый поиск (PostgreSQL tsvector / rank)
GET /api/notes/?search=PostgreSQL

# Фильтрация по категории (slug)
GET /api/notes/?category=backend

# Фильтрация по тегу
GET /api/notes/?tag=python

# Фильтрация по закреплённым и избранным
GET /api/notes/?is_pinned=true&is_favorite=true

# Фильтрация по датам
GET /api/notes/?created_after=2026-01-01T00:00:00Z&created_before=2026-12-31T23:59:59Z

# Сортировка
GET /api/notes/?ordering=-updated_at
```

---

## Тестирование и проверка качества

Для контроля качества подготовлены команды в `Makefile`:

```bash
# Проверка стиля и импортов
make lint

# Автоматическое форматирование
make format

# Проверка статической типизации Mypy (strict)
make type-check

# Запуск тестов с отчётом о покрытии
make test

# Комплексный запуск всех проверок
make all
```

---

## Лицензия

Проект распространяется под открытой лицензией [MIT License](LICENSE).
