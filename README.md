# Inventory Management System

A full-stack inventory management portfolio project built with Python, FastAPI, SQLAlchemy, SQLite/PostgreSQL, HTML, CSS, and JavaScript.

> Project status: starter implementation. Run the app and tests in your environment before describing any results in your resume.

## Features

- Create, read, update, and delete products
- SKU uniqueness validation
- Search by product name, SKU, or category
- Filter by category and low-stock status
- Dashboard metrics: product count, total units, inventory value, and low-stock count
- Stock additions/removals with a movement history
- Prevent negative stock and invalid prices/quantities
- Responsive browser UI
- API documentation through Swagger UI
- Automated API tests with pytest
- Docker and Docker Compose configuration

## Architecture

```text
Browser (HTML/CSS/JavaScript)
            |
            | HTTP / JSON
            v
       FastAPI routes
            |
     Pydantic validation
            |
     SQLAlchemy ORM
            |
    SQLite or PostgreSQL
```

## Requirements

- Python 3.11 or newer (the Docker image uses Python 3.12)
- Git
- Optional: Docker Desktop for containerized PostgreSQL

## Run locally with SQLite

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd inventory-management-api
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the application

```bash
uvicorn app.main:app --reload
```

Open:
- Web interface: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

SQLite database file `inventory.db` is created in the working directory on startup.

## Run tests

```bash
pytest -v
```

Tests use a separate in-memory SQLite database. They do not need your local inventory database.

## Run with Docker Compose and PostgreSQL

Ensure Docker Desktop or Docker Engine is running, then:

```bash
docker compose up --build
```

Open http://localhost:8000. Stop containers with:

```bash
docker compose down
```

PostgreSQL data is stored in a Docker volume. To delete the volume and all local database data, run `docker compose down -v`.

For local development, change `POSTGRES_PASSWORD` from the default before using this setup for anything beyond a personal machine. Do not commit production secrets.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/products` | List/search/filter products |
| POST | `/api/products` | Create product |
| GET | `/api/products/{id}` | Get product details |
| PATCH | `/api/products/{id}` | Update product metadata |
| DELETE | `/api/products/{id}` | Delete product |
| POST | `/api/products/{id}/stock` | Add/remove stock |
| GET | `/api/products/{id}/movements` | View stock movement history |
| GET | `/api/dashboard` | Dashboard metrics |
| GET | `/api/categories` | Product categories |
| GET | `/health` | Health check |

### Example: create a product

```bash
curl -X POST http://127.0.0.1:8000/api/products ^
  -H "Content-Type: application/json" ^
  -d "{\"sku\":\"KEY-001\",\"name\":\"Mechanical Keyboard\",\"category\":\"Electronics\",\"description\":\"USB keyboard\",\"price\":2500,\"quantity\":10,\"reorder_level\":3}"
```

For macOS/Linux, use `\\` at line endings instead of `^`, or send the request from Swagger UI at `/docs`.

### Example: remove stock

```json
{
  "change": -2,
  "reason": "sale",
  "note": "Order reference"
}
```

Stock adjustments must be non-zero. A request that would reduce stock below zero is rejected.

## Configuration

Set `DATABASE_URL` to select a database. Examples:

```text
sqlite:///./inventory.db
postgresql+psycopg://user:password@localhost:5432/inventory
```

Never commit `.env` files or real credentials. `.env.example` is a template; the application reads environment variables supplied by your shell or deployment environment.

## Deployment checklist

1. Push the code to a GitHub repository.
2. Choose a Python-capable hosting provider that supports a persistent database or provision managed PostgreSQL.
3. Set `DATABASE_URL` using the provider's environment-variable settings.
4. Use the start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
5. Verify `/health`, `/docs`, and the browser UI after deployment.
6. Keep secrets out of Git and use a strong database password.
7. Add database migrations (Alembic), authentication/authorization, backups, and monitoring before treating this as a production business system.

The current starter creates tables automatically on startup. For production, use Alembic migrations rather than relying on `create_all`.

## Suggested improvements

- User login and role-based permissions
- Supplier and purchase-order management
- CSV import/export
- Pagination metadata and server-side sorting
- Alembic migrations
- Audit log retention and safer product archival
- Currency-aware decimal storage instead of floating-point prices
- CI workflow to run tests on each push
- Rate limiting and security headers

## Portfolio presentation

After you have run and verified the project, add screenshots, test output, and the deployed URL here. Only report measured test results or performance numbers you have actually observed.

Resume bullet template (fill in only after verification):

- Built a full-stack inventory management application using Python, FastAPI, SQLAlchemy, and PostgreSQL, with product CRUD, stock movement tracking, low-stock filtering, and automated API tests.
