# DocuSense API

A FastAPI REST API application for document management with semantic search and question-answering capabilities, powered by PostgreSQL + pgvector.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL + pgvector** - Relational database with vector similarity search
- **SQLAlchemy** - Async ORM for database operations
- **Sentence Transformers** - Local embedding generation for semantic search
- **Text Extraction** - Extract text from PDFs (PyMuPDF) and images (EasyOCR)
- **Question Answering** - Answer questions about documents using DistilBERT QA
- **Session-based Document Management** - Upload and retrieve documents by session
- **Rate Limiting** - Configurable rate limiting with slowapi
- **Response Caching** - TTL-based caching for QA responses
- **Swagger UI** - Interactive API documentation at `/docs`
- **ReDoc** - Alternative API documentation at `/redoc`
- **Docker Support** - Production and development Dockerfiles
- **UV Package Manager** - Fast Python package management
- **Pytest** - Comprehensive unit testing
- **Alembic** - Database migrations

## Quick Start

### Prerequisites

- Python 3.11+
- [UV Package Manager](https://github.com/astral-sh/uv)

### Clone the Repository

```bash
git clone <repository-url>
cd DocuSense
```

### Environment Variables (Optional)

The application has sensible default values for all settings, so a `.env` file is **not required** for local development. However, you can create one to customize the configuration:

```bash
cp .env.example .env
```

See the [Environment Variables](#environment-variables) section for all available options.

---

## Option 1: Docker Setup (Recommended)

This is the easiest way to get started. Docker handles all dependencies including PostgreSQL with pgvector.

### Prerequisites for Docker Setup

- Docker & Docker Compose

### Production Mode

Start both PostgreSQL and the API with a single command:

```bash
docker-compose up --build
```

### Development Mode (with Hot Reload)

For development with automatic code reloading:

```bash
docker-compose --profile dev up api-dev db --build
```

### Hybrid Mode (Docker DB + Local API)

Run only the database in Docker while running the API locally for faster development iteration:

1. **Start PostgreSQL with pgvector:**
   ```bash
   docker-compose up db -d
   ```

2. **Install Python dependencies:**
   ```bash
   uv sync --dev
   ```

3. **Run the API locally:**
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## Option 2: Local Setup (Without Docker)

If you prefer to run everything locally without Docker, follow these steps to install and configure PostgreSQL with pgvector manually.

### Prerequisites for Local Setup

- Python 3.11+
- [UV Package Manager](https://github.com/astral-sh/uv)
- PostgreSQL 16+ with pgvector extension

### Step 1: Install PostgreSQL 16+

**Windows:**
- Download from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)
- Or use Chocolatey: `choco install postgresql16`

**macOS:**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql-16 postgresql-contrib-16
sudo systemctl start postgresql
```

### Step 2: Install pgvector Extension

**Windows:**
- Download prebuilt binaries from [pgvector releases](https://github.com/pgvector/pgvector/releases)
- Or build from source (requires Visual Studio Build Tools)

**macOS:**
```bash
brew install pgvector
```

**Ubuntu/Debian:**
```bash
sudo apt install postgresql-16-pgvector
```

**From source (any platform):**
```bash
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install  # may require sudo
```

### Step 3: Create Database and User

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# In psql, run:
CREATE USER docusense WITH PASSWORD 'docusense';
CREATE DATABASE docusense OWNER docusense;
GRANT ALL PRIVILEGES ON DATABASE docusense TO docusense;
\q
```

### Step 4: Initialize Database Schema

Use the provided initialization script:

```bash
# Connect to the docusense database and run the init script
psql -U docusense -d docusense -f scripts/init-db.sql
```

This script will:
- Enable the `pgvector` extension (`CREATE EXTENSION IF NOT EXISTS vector;`)
- Create the `sessions`, `documents`, and `document_chunks` tables
- Set up indexes including the vector similarity search index

### Step 5: Configure Environment

Ensure your `.env` has the correct `DATABASE_URL` for local PostgreSQL:
```
DATABASE_URL=postgresql+asyncpg://docusense:docusense@localhost:5432/docusense
```

### Step 6: Install Python Dependencies

```bash
uv sync --dev
```

### Step 7: Run the API

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Accessing the API

- **API Root:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Root
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |

### Authentication (v1)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/token` | Login and get JWT access token |
| GET | `/api/v1/auth/me` | Get current authenticated user |
| GET | `/api/v1/auth/verify` | Verify token validity |

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

### Question Answering (v1)
| Method | Endpoint             | Description |
|--------|----------------------|-------------|
| POST | `/api/v1/ask`        | Ask a question about uploaded documents |
| GET | `/api/v1/ask/status` | Get QA service status |
| DELETE | `/api/v1/ask/cache`  | Clear the QA answer cache |

### Items (v1)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/items/` | List all items |
| POST | `/api/v1/items/` | Create new item |
| GET | `/api/v1/items/{id}` | Get item by ID |
| PUT | `/api/v1/items/{id}` | Update item |
| DELETE | `/api/v1/items/{id}` | Delete item |

## Usage

The easiest way to explore and test the API is through the interactive **Swagger UI** at [http://localhost:8000/docs](http://localhost:8000/docs).

Swagger UI provides:
- Interactive documentation for all endpoints
- Built-in request builder with parameter validation
- One-click "Try it out" functionality
- Response examples and schemas

Alternatively, use **ReDoc** at [http://localhost:8000/redoc](http://localhost:8000/redoc) for a clean, readable API reference.

## Testing

### Uploading a Document

Use the Swagger UI to upload documents via the `/api/v1/upload` endpoint:

![Uploading a document via Swagger UI](docs/images/upload-document.png)

The upload endpoint:
1. Accepts one or more files (PDF, images, text files)
2. Returns a `session_id` for tracking your documents
3. Automatically extracts text (with OCR for scanned documents)
4. Chunks and embeds the content for semantic search

Use the returned `session_id` in the `X-Session-ID` header for subsequent requests.

### Asking a Question

Use the Swagger UI to ask questions about your documents via the `/api/v1/ask` endpoint:

![Asking a question via Swagger UI](docs/images/ask-question.png)

The ask endpoint:
1. Requires the `session_id` obtained during document upload
2. Optionally accepts specific `document_ids` to narrow the search scope
3. Uses semantic search to find relevant document chunks
4. Generates an answer using the configured LLM (or extractive QA as fallback)
5. Returns the answer with confidence score and source references

### Running Unit Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_qa_service.py -v

# Run text extraction tests
uv run pytest tests/test_text_extraction.py -v
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

## JWT Authentication

DocuSense includes JWT-based authentication for protecting API endpoints.

### Demo Credentials

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | admin |
| `user` | `user123` | user |

### Using Authentication in Swagger UI

1. Navigate to http://localhost:8000/docs
2. Click the **"Authorize"** button (🔓 icon at top-right)
3. Enter credentials (e.g., `admin` / `admin123`)
4. Click **"Authorize"**
5. All protected endpoints will now include the JWT token automatically

### Programmatic Authentication

```bash
# Get a token
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Use the token
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <your-token>"
```

### Protected Endpoints

All API endpoints (except health checks) require authentication:

| Endpoint | Auth Required | Role |
|----------|---------------|------|
| `GET /` | No | - |
| `GET /api/v1/health/*` | No | - |
| `POST /api/v1/auth/token` | No | - |
| `GET /api/v1/auth/me` | Yes | Any |
| `GET /api/v1/auth/verify` | Yes | Any |
| `POST /api/v1/upload` | Yes | Any |
| `GET /api/v1/upload` | Yes | Any |
| `GET /api/v1/upload/{id}` | Yes | Any |
| `DELETE /api/v1/upload/{id}` | Yes | Any |
| `POST /api/v1/upload/session` | Yes | Any |
| `POST /api/v1/ask` | Yes | Any |
| `GET /api/v1/ask/status` | Yes | Any |
| `DELETE /api/v1/ask/cache` | Yes | **Admin** |

To protect additional endpoints, add the `get_current_active_user` dependency:

```python
from app.core.security import User, get_current_active_user

@router.get("/protected")
async def protected_endpoint(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return {"user": current_user.username}
```

### JWT Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | (change in production) | Secret key for signing tokens |
| `JWT_ALGORITHM` | HS256 | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Token expiration time |

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
| `OCR_USE_GPU` | false | Enable GPU for OCR |
| `OCR_LANGUAGES` | en | OCR language codes |
| `QA_MODEL_NAME` | distilbert-base-cased-distilled-squad | QA model |
| `QA_MAX_CONTEXT_LENGTH` | 512 | Max context tokens for QA |
| `QA_TOP_K_CHUNKS` | 5 | Number of chunks to retrieve |
| `RATE_LIMIT_ENABLED` | true | Enable rate limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | 30 | Rate limit threshold |
| `CACHE_TTL_SECONDS` | 3600 | Cache TTL (1 hour) |
| `CACHE_MAX_SIZE` | 1000 | Max cached responses |

## Supported File Types

### Documents
- `.txt` - Plain text
- `.md` - Markdown
- `.pdf` - PDF documents (with OCR fallback for scanned pages)
- `.doc` / `.docx` - Word documents (extraction coming soon)

### Images (OCR)
- `.png` - PNG images
- `.jpg` / `.jpeg` - JPEG images
- `.tiff` - TIFF images
- `.bmp` - Bitmap images

## ML Models

### Text Extraction
- **PyMuPDF** - Fast PDF text extraction
- **EasyOCR** - OCR for images and scanned documents

### Embeddings
- **all-MiniLM-L6-v2** - Sentence transformer for semantic search (384 dimensions)

### Question Answering (Hybrid RAG)

DocuSense supports two QA modes:

1. **Generative RAG** (recommended) - Uses LLMs for natural language answers
   - **Ollama** - Local LLM inference (Mistral, Llama, etc.)
   - **OpenAI** - Cloud-based GPT models

2. **Extractive QA** (legacy) - Extracts answer spans from context
   - **distilbert-base-cased-distilled-squad** - DistilBERT fine-tuned on SQuAD

The system automatically falls back to extractive QA if the LLM is unavailable.

## Hybrid RAG Configuration

### Using Ollama (Local LLM - Default)

1. **Install Ollama:**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Windows - download from https://ollama.com/download
   ```

2. **Pull a model:**
   ```bash
   ollama pull mistral
   # Or other models: llama3, phi3, gemma2, etc.
   ```

3. **Configure environment:**
   ```bash
   LLM_PROVIDER=ollama
   LLM_MODEL=mistral
   LLM_BASE_URL=http://localhost:11434
   ```

### Using OpenAI

1. **Install OpenAI dependency:**
   ```bash
   uv sync --extra openai
   ```

2. **Configure environment:**
   ```bash
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-3.5-turbo
   OPENAI_API_KEY=sk-your-api-key
   ```

### LLM Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | ollama | LLM provider: `ollama`, `openai`, or `extractive` (legacy) |
| `LLM_MODEL` | mistral | Model name for the provider |
| `LLM_BASE_URL` | http://localhost:11434 | Ollama API base URL |
| `OPENAI_API_KEY` | - | OpenAI API key (required for openai provider) |
| `LLM_TEMPERATURE` | 0.1 | Generation temperature (0-1) |
| `LLM_MAX_TOKENS` | 500 | Max tokens for generated answer |

## License

MIT License
