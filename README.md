# DocuSense API

A FastAPI REST API application with Docker support, Swagger documentation, and pytest unit testing.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **Swagger UI** - Interactive API documentation at `/docs`
- **ReDoc** - Alternative API documentation at `/redoc`
- **Docker Support** - Production and development Dockerfiles
- **UV Package Manager** - Fast Python package management
- **Pytest** - Comprehensive unit testing

## Project Structure

```
DocuSense/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py    # API v1 router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py    # Health check endpoints
│   │           └── items.py     # Items CRUD endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Application configuration
│   ├── models/
│   │   └── __init__.py
│   └── schemas/
│       ├── __init__.py
│       └── item.py          # Pydantic schemas
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_main.py         # Root endpoint tests
│   ├── test_health.py       # Health endpoint tests
│   └── test_items.py        # Items endpoint tests
├── Dockerfile               # Production Dockerfile
├── Dockerfile.dev           # Development Dockerfile
├── docker-compose.yml       # Docker Compose configuration
├── pyproject.toml           # Project configuration & dependencies
├── uv.toml                  # UV-specific settings
├── uv.lock                  # Dependency lock file
├── .env.example             # Example environment variables
├── .gitignore
└── .dockerignore
```

## Quick Start

### Prerequisites

- Python 3.11+
- [UV Package Manager](https://github.com/astral-sh/uv)
- Docker (optional, for containerized deployment)

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

### Running the Application

#### Using UV (Development)

```bash
# Run with hot reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Using Docker

```bash
# Build and run production container
docker-compose up --build

# Run development container with hot reload
docker-compose --profile dev up api-dev --build
```

### Accessing the API

Once running, access the API at:

- **API Root:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

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

### Items (v1)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/items/` | List all items |
| GET | `/api/v1/items/{id}` | Get item by ID |
| POST | `/api/v1/items/` | Create new item |
| PUT | `/api/v1/items/{id}` | Update item |
| DELETE | `/api/v1/items/{id}` | Delete item |

## Testing

### Run All Tests

```bash
uv run pytest
```

### Run Tests with Coverage

```bash
uv run pytest --cov=app --cov-report=html
```

### Run Specific Test File

```bash
uv run pytest tests/test_items.py -v
```

### Run Tests with Output

```bash
uv run pytest -v -s
```

## Development

### Code Formatting & Linting

```bash
# Run ruff linter
uv run ruff check .

# Run ruff formatter
uv run ruff format .
```

### Adding Dependencies

```bash
# Add a production dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | DocuSense API | Application name |
| `APP_VERSION` | 0.1.0 | Application version |
| `DEBUG` | false | Enable debug mode |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `API_PREFIX` | /api/v1 | API prefix |

## License

MIT License
