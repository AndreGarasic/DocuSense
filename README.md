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

### Question Answering (v1)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/asl` | Ask a question about uploaded documents |
| GET | `/api/v1/asl/status` | Get QA service status |
| DELETE | `/api/v1/asl/cache` | Clear the QA answer cache |

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

# Upload an image for OCR
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "X-Session-ID: your-session-id" \
  -F "files=@scanned_receipt.png"
```

### Ask Questions

```bash
# Ask a question about uploaded documents
curl -X POST "http://localhost:8000/api/v1/asl" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: your-session-id" \
  -d '{"question": "What is the total amount?"}'

# Ask about specific documents
curl -X POST "http://localhost:8000/api/v1/asl" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: your-session-id" \
  -d '{"question": "Who are the parties in this contract?", "document_ids": [1, 2]}'

# Check QA service status
curl -X GET "http://localhost:8000/api/v1/asl/status"
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

### Question Answering
- **distilbert-base-cased-distilled-squad** - DistilBERT fine-tuned on SQuAD

## License

MIT License
