# DocuSense API

A FastAPI REST API application for document management with semantic search capabilities, powered by PostgreSQL + pgvector.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL + pgvector** - Relational database with vector similarity search
- **SQLAlchemy** - Async ORM for database operations
- **Sentence Transformers** - Local embedding generation for semantic search
- **Session-based Document Management** - Upload and retrieve documents by session
- **Swagger UI** - Interactive API documentation at `/docs`
- **ReDoc** - Alternative API documentation at `/redoc`
- **Docker Support** - Production and development Dockerfiles
- **UV Package Manager** - Fast Python package management
- **Pytest** - Comprehensive unit testing
- **Alembic** - Database migrations

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL + pgvector                        │
├─────────────────────────────────────────────────────────────────┤
│  RELATIONAL TABLES              │  VECTOR-ENABLED TABLE         │
│  ─────────────────              │  ────────────────────         │
│  • sessions                     │  • document_chunks            │
│    - id (UUID)                  │    - id                       │
│    - created_at                 │    - document_id (FK)         │
│    - expires_at                 │    - chunk_index              │
│  • documents                    │    - content (text)           │
│    - id                         │    - embedding (vector(384))  │
│    - session_id (FK)            │    - metadata (jsonb)         │
│    - filename                   │                               │
│    - file_path                  │                               │
│    - content_type               │                               │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
DocuSense/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── api/
│   │   └── v1/
│   │       ├── router.py        # API v1 router
│   │       └── endpoints/
│   │           ├── health.py    # Health check endpoints
│   │           ├── items.py     # Items CRUD endpoints
│   │           └── upload.py    # Document upload endpoints
│   ├── core/
│   │   └── config.py            # Application configuration
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py              # SQLAlchemy base model
│   │   └── session.py           # Database session management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── session.py           # Session model
│   │   ├── document.py          # Document model
│   │   └── document_chunk.py    # Document chunk model with vectors
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── item.py              # Item schemas
│   │   ├── session.py           # Session schemas
│   │   └── document.py          # Document schemas
│   └── services/
│       ├── __init__.py
│       ├── session_service.py   # Session business logic
│       ├── document_service.py  # Document business logic
│       └── embedding_service.py # Embedding generation
├── alembic/
│   ├── env.py                   # Alembic environment
│   ├── script.py.mako           # Migration template
│   └── versions/                # Migration files
├── scripts/
│   └── init-db.sql              # Database initialization
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   ├── test_main.py
│   ├── test_health.py
│   ├── test_items.py
│   └── test_upload.py           # Upload endpoint tests
├── uploads/                     # Document storage (gitignored)
├── Dockerfile
├── Dockerfile.dev
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
└── .env.example
```

## Quick Start

### Prerequisites

- Python 3.11+
- [UV Package Manager](https://github.com/astral-sh/uv)
- Docker & Docker Compose
- PostgreSQL 16+ with pgvector (or use Docker)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd DocuSense
   ```

2. **Install dependencies with UV:**
   ```bash
   uv sync --dev
   ```

3. **Copy environment variables:**
   ```bash
   cp .env.example .env
   ```

### Running with Docker (Recommended)

```bash
# Start PostgreSQL and API
docker-compose up --build

# Or run in development mode with hot reload
docker-compose --profile dev up api-dev db --build
```

### Running Locally

1. **Start PostgreSQL with pgvector:**
   ```bash
   docker-compose up db -d
   ```

2. **Run the API:**
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Accessing the API

- **API Root:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Root
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |

### Health (v1)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health/health` | Health check |
| GET | `/api/v1/health/ready` | Readiness check |

### Upload (v1)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload` | Upload one or more documents |
| GET | `/api/v1/upload` | List documents (requires X-Session-ID header) |
| GET | `/api/v1/upload/{id}` | Get document by ID |
| DELETE | `/api/v1/upload/{id}` | Delete document |
| POST | `/api/v1/upload/session` | Create a new session |

### Items (v1)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/items/` | List all items |
| POST | `/api/v1/items/` | Create new item |
| GET | `/api/v1/items/{id}` | Get item by ID |
| PUT | `/api/v1/items/{id}` | Update item |
| DELETE | `/api/v1/items/{id}` | Delete item |

## Usage Examples

### Upload Documents

```bash
# Upload a single file (creates new session)
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "files=@document.txt"

# Upload multiple files
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "files=@doc1.txt" \
  -F "files=@doc2.pdf"

# Upload to existing session
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "X-Session-ID: your-session-id" \
  -F "files=@document.txt"
```

### List Documents

```bash
curl -X GET "http://localhost:8000/api/v1/upload" \
  -H "X-Session-ID: your-session-id"
```

### Create Session

```bash
curl -X POST "http://localhost:8000/api/v1/upload/session?expires_in_hours=48"
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_upload.py -v
```

## Database Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | DocuSense API | Application name |
| `APP_VERSION` | 0.1.0 | Application version |
| `DEBUG` | false | Enable debug mode |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `DATABASE_URL` | postgresql+asyncpg://... | Database connection URL |
| `UPLOAD_DIR` | uploads | Directory for file storage |
| `MAX_FILE_SIZE` | 52428800 | Max upload size (50MB) |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Sentence transformer model |
| `EMBEDDING_DIMENSION` | 384 | Embedding vector dimension |

## Supported File Types

- `.txt` - Plain text
- `.md` - Markdown
- `.pdf` - PDF documents (extraction coming soon)
- `.doc` / `.docx` - Word documents (extraction coming soon)

## License

MIT License
