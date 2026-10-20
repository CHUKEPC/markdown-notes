# Markdown Note Service

[![CI](https://github.com/CHUKEPC/markdown-notes/actions/workflows/ci.yml/badge.svg)](https://github.com/CHUKEPC/markdown-notes/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5](https://img.shields.io/badge/Django-5.0+-092e20.svg?style=flat&logo=Django&logoColor=white)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.15+-red.svg)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1.svg?style=flat&logo=PostgreSQL&logoColor=white)](https://www.postgresql.org/)
[![Bleach](https://img.shields.io/badge/Bleach-6.1+-orange.svg)](https://github.com/mozilla/bleach)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust, production-grade Markdown note-taking and knowledge base backend built with **Django 5**, **Django REST Framework**, and **PostgreSQL**. Features server-side Markdown-to-HTML rendering with XSS sanitization via **Bleach**, full-text search leveraging PostgreSQL `tsvector`/`tsquery`, version control with unified diff history and rollback, secret public sharing links with optional expiration, tag and category taxonomy, import/export (JSON, Markdown, ZIP archives), and token-based authentication.

---

## Features

- **Markdown to HTML Pipeline**: Converts raw Markdown to structured HTML with standard syntax extensions (fenced code, tables, autolinks, lists, tasklists), sanitized via Bleach to guarantee defense against XSS.
- **Full-Text Search (FTS)**: Fast PostgreSQL full-text search engine utilizing weighted `SearchVector` (title weighted higher than body content) and `SearchRank` ordering, with an automatic fallback for testing environments.
- **Revision History & Versioning**: Every note edit creates a snapshot capturing sequential versions, modification timestamps, summaries, and unified text diffs against prior versions. Supports 1-click version rollbacks.
- **Secure Public Link Sharing**: Share individual notes via unguessable 64-character tokens with optional expiration dates (1–365 days). Read-only public access without requiring an account.
- **Taxonomy & Organization**: Organize notes into categories with custom colors and slugs, and cross-cutting many-to-many tags.
- **Favorites & Pinned Notes**: Pin important notes to stay at the top of listings and mark favorites with dedicated filter flags.
- **Import & Export**:
  - Export single notes as raw Markdown (`.md`) with YAML frontmatter or as structured JSON.
  - Export all user notes as a downloadable `.zip` archive containing individual Markdown files.
  - Import notes from uploaded Markdown files (extracting title, tags, and category from frontmatter) or bulk JSON payloads.
- **Filtering & Cursor Pagination**: Flexible filtering by tag, category, status, and creation/update dates via `django-filter`. Supports both standard page-number pagination and cursor-based pagination.
- **Token Authentication**: Secure registration, login, logout, and profile management using DRF TokenAuth (`Token <key>`).
- **Strict Data Isolation**: Object-level permissions ensuring users can only read, modify, and delete their own categories, tags, and notes.

---

## Tech Stack

| Component | Technology | Description |
|---|---|---|
| **Framework** | Django 5.2+ | High-level Python web framework |
| **REST API** | Django REST Framework 3.18+ | Web APIs with serializers, viewsets, and token auth |
| **Database** | PostgreSQL 16+ | Relational storage with `tsvector`/`tsquery` search |
| **Markdown Engine** | Python Markdown | Markdown processor with tables, code, and list extensions |
| **Sanitizer** | Bleach 6.4+ | Whitelist-based HTML sanitization preventing XSS attacks |
| **Filtering** | django-filter 26+ | Dynamic query parameter filtering |
| **Typing & Linting** | Mypy (strict mode) & Ruff | Type enforcement with `django-stubs` and high-speed linting |
| **Testing** | pytest, pytest-django, pytest-cov | 50 comprehensive tests with **92% code coverage** |
| **Deployment** | Docker & Docker Compose | Multi-stage Dockerfile and full stack container orchestration |

---

## Architecture & Project Structure

The project follows clean separation of concerns within a standard Django modular architecture. Business logic resides in `services/`, markdown rendering in `renderers/`, version control in `versioning/`, and search logic in `search.py`.

```
markdown-notes/
├── src/
│   ├── manage.py                     # Root management script delegating to markdown_notes
│   └── markdown_notes/
│       ├── __init__.py
│       ├── manage.py                 # Django management script
│       ├── config/                   # Project settings and root URL configuration
│       │   ├── __init__.py
│       │   ├── settings.py           # Database, DRF, auth, and app configuration
│       │   ├── urls.py               # Root URL router
│       │   └── wsgi.py               # WSGI application entrypoint
│       ├── notes/                    # Core notes application
│       │   ├── __init__.py
│       │   ├── apps.py
│       │   ├── models.py             # Note, Category, Tag, NoteVersion models
│       │   ├── serializers.py        # Model serializers and input validation
│       │   ├── views.py              # ModelViewSets and APIViews
│       │   ├── urls.py               # Router and endpoint registration
│       │   ├── filters.py            # django-filter FilterSet with search hooks
│       │   ├── services.py           # NoteService business operations
│       │   ├── search.py             # PostgreSQL tsvector/tsquery logic
│       │   ├── versioning.py         # Snapshot creation and difflib text diffs
│       │   ├── renderers.py          # Markdown rendering + Bleach sanitization
│       │   └── permissions.py        # IsOwner and IsOwnerOrSharedReadOnly
│       ├── users/                    # Authentication and accounts application
│       │   ├── __init__.py
│       │   ├── apps.py
│       │   ├── models.py             # Custom User model
│       │   ├── serializers.py        # Register, login, and profile serializers
│       │   ├── views.py              # Register, login, logout, me views
│       │   └── urls.py               # Auth endpoint routing
│       └── utils/                    # Shared utilities
│           ├── __init__.py
│           ├── apps.py
│           └── pagination.py         # Standard and cursor pagination classes
├── tests/                            # Pytest automated test suite (50 tests)
│   ├── conftest.py                   # Client fixtures, mock users, test data
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
├── docker-compose.yml                # Full stack container configuration
├── Dockerfile                        # Multi-stage container build
├── Makefile                          # Task automation commands
├── pyproject.toml                    # Dependencies, ruff, mypy, and pytest configs
├── .env.example                      # Documented environment variables template
└── README.md
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16+ (or Docker)

### Option 1: Running with Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/CHUKEPC/markdown-notes.git
   cd markdown-notes
   ```

2. **Start services**:
   ```bash
   docker compose up -d --build
   ```

3. **Verify API health**:
   ```bash
   curl http://localhost:8000/api/health/
   ```

---

### Option 2: Local Virtual Environment Setup

1. **Create and activate Python virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -e ".[dev]"
   ```

3. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL credentials or omit DATABASE_URL to use SQLite fallback
   ```

4. **Apply database migrations**:
   ```bash
   python src/markdown_notes/manage.py migrate
   ```

5. **Start the development server**:
   ```bash
   python src/markdown_notes/manage.py runserver 0.0.0.0:8000
   ```

---

## REST API Reference

All protected endpoints require an authorization header:
```http
Authorization: Token <your_token_here>
```

### 1. Authentication & Profiles (`/api/users/`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/users/register/` | Register new user account and obtain token | No |
| `POST` | `/api/users/login/` | Authenticate with credentials and obtain token | No |
| `POST` | `/api/users/logout/` | Invalidate and delete active user token | Yes |
| `GET` | `/api/users/me/` | Retrieve authenticated user profile | Yes |
| `PATCH` | `/api/users/me/` | Update profile fields (first_name, bio, avatar) | Yes |

#### Registration Request Example
```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "developer",
    "email": "dev@example.com",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "bio": "Backend software engineer"
  }'
```

---

### 2. Notes CRUD & Actions (`/api/notes/`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/notes/` | List notes with pagination, search, and filtering |
| `POST` | `/api/notes/` | Create a new note (renders HTML & sets version 1) |
| `GET` | `/api/notes/{id}/` | Retrieve full note details with rendered HTML |
| `PUT` | `/api/notes/{id}/` | Update note (creates new version snapshot with diff) |
| `DELETE` | `/api/notes/{id}/` | Delete note |
| `POST` | `/api/notes/{id}/pin/` | Toggle pinned status |
| `POST` | `/api/notes/{id}/favorite/` | Toggle favorite status |
| `POST` | `/api/notes/{id}/share/` | Create or update public share link |
| `POST` | `/api/notes/{id}/revoke-share/` | Deactivate public share link |
| `GET` | `/api/notes/{id}/versions/` | List revision history of note |
| `GET` | `/api/notes/{id}/versions/{version}/` | Get specific historical snapshot |
| `POST` | `/api/notes/{id}/versions/{version}/revert/` | Revert note to chosen version |
| `GET` | `/api/notes/{id}/versions/{v1}/diff/?compare_to={v2}` | Get unified diff between versions |
| `GET` | `/api/notes/{id}/export/?export_format=markdown` | Export note as Markdown with frontmatter |
| `GET` | `/api/notes/{id}/export/?export_format=json` | Export note as JSON |
| `GET` | `/api/notes/export-all/` | Download ZIP archive of all user notes |
| `POST` | `/api/notes/import/` | Import note from `.md` file or JSON array |
| `GET` | `/api/notes/shared/{share_token}/` | **Public read endpoint** for shared note |

#### Create Note Example
```bash
curl -X POST http://localhost:8000/api/notes/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Django Architecture Overview",
    "content": "# Architecture\n\n- Models\n- Views\n- Services\n\n```python\nprint(\"Clean Architecture\")\n```",
    "category_id": 1,
    "tags": ["Django", "Architecture"],
    "is_pinned": true
  }'
```

#### Public Share Link Example
```bash
# Generate share link expiring in 14 days
curl -X POST http://localhost:8000/api/notes/<note_id>/share/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"expires_in_days": 14}'

# Public unauthenticated view
curl http://localhost:8000/api/notes/shared/<share_token>/
```

---

### 3. Categories & Tags (`/api/categories/`, `/api/tags/`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/categories/` | List user categories with notes count |
| `POST` | `/api/categories/` | Create a category (auto-generates slug) |
| `GET` | `/api/categories/{id}/` | Retrieve category details |
| `PUT` | `/api/categories/{id}/` | Update category name, color, description |
| `DELETE` | `/api/categories/{id}/` | Delete category |
| `GET` | `/api/tags/` | List user tags with notes count |
| `POST` | `/api/tags/` | Create a new tag |
| `DELETE` | `/api/tags/{id}/` | Delete tag |

---

### 4. Search and Filtering

Filter notes using flexible query parameters:
```bash
# Full-text search (PostgreSQL tsvector / rank)
GET /api/notes/?search=PostgreSQL

# Filter by category slug
GET /api/notes/?category=backend

# Filter by tag label
GET /api/notes/?tag=python

# Filter by pinned or favorites
GET /api/notes/?is_pinned=true&is_favorite=true

# Filter by date ranges
GET /api/notes/?created_after=2026-01-01T00:00:00Z&created_before=2026-12-31T23:59:59Z

# Ordering
GET /api/notes/?ordering=-updated_at
```

---

## Development & Testing

Automated commands are configured via `Makefile`:

```bash
# Run linter and check formatting
make lint

# Auto-format and fix lint issues
make format

# Run static type checking with Mypy in strict mode
make type-check

# Run full pytest suite with coverage report
make test

# Run all quality checks (lint + type-check + test)
make all
```

### Test Coverage Summary
```
Name                                 Stmts   Miss  Cover
--------------------------------------------------------
src/markdown_notes/notes/models.py      74      0   100%
src/markdown_notes/notes/renderers.py   11      0   100%
src/markdown_notes/notes/versioning.py  28      0   100%
src/markdown_notes/notes/serializers.py 56      0   100%
src/markdown_notes/notes/services.py   179     12    93%
src/markdown_notes/notes/views.py      176     11    94%
src/markdown_notes/notes/filters.py     30      3    90%
src/markdown_notes/notes/permissions.py 19      1    95%
src/markdown_notes/users/models.py      13      0   100%
src/markdown_notes/users/views.py       45      1    98%
src/markdown_notes/users/serializers.py 42      1    98%
src/markdown_notes/utils/pagination.py   9      0   100%
--------------------------------------------------------
TOTAL                                  812     64    92%
```

---

## License

This project is open-source and licensed under the [MIT License](LICENSE).
