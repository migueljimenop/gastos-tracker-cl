# Project Guidelines

## Architecture

FastAPI expense tracker for Chilean Santander and Falabella bank accounts. SQLite + SQLAlchemy 2.0 ORM, Pydantic v2 schemas, custom JWT auth.

```
gastos_tracker/
  app/
    models.py        # SQLAlchemy models (User, Category, Transaction, Budget)
    schemas.py       # Pydantic request/response DTOs
    config.py        # Pydantic Settings (.env-based)
    dependencies.py  # get_db(), get_current_user()
    routers/         # FastAPI routers (one per resource)
    services/        # Business logic (categorizer, reports, exporter, alerts)
    importers/       # File parsers (Excel/CSV) — inherit BaseImporter
    scrapers/        # Playwright bank scrapers — inherit BaseScraper
    static/          # Vanilla JS + Tailwind frontend
  tests/             # Pytest + TestClient, fixture-based dependency overrides
```

## Code Style

- **Language**: Spanish for UI text, error messages, field names, and comments. English for code identifiers (class names, function names, variable names).
- **Python**: Modern type hints, `Mapped[]` columns, Pydantic v2 (`model_config`, `from_attributes=True`).
- **Schemas**: `{Entity}Create`, `{Entity}Update`, `{Entity}Out` naming convention.
- **Routers**: One file per resource under `app/routers/`. Protected routes use `Depends(get_current_user)`.
- **Services**: Business logic lives in `app/services/`, not in routers.
- **Importers/Scrapers**: Inherit from abstract base class. Use `_parse_chilean_amount()` and `_parse_chilean_date()` helpers for Chilean formats (dots as thousands separator, DD/MM/YYYY dates).

## Build and Test

```bash
cd gastos_tracker
pip install -r requirements.txt
uvicorn app.main:app --reload          # Run dev server
pytest -v                               # Run tests
```

- Tests override `get_db` and `get_current_user` dependencies via fixtures in `tests/conftest.py` — no real auth in tests.
- `asyncio_mode = auto` in `pytest.ini` — no need for `@pytest.mark.asyncio`.
- Test pattern: create → get → list → filter → update → delete.

## Conventions

- All secrets and bank credentials go in `.env` (never hardcode). Config validated via `app/config.py` Pydantic Settings.
- Transactions use `external_id` for deduplication on import.
- Chilean money format: dots for thousands (`1.234.567`), commas for decimals, parentheses for negative amounts `(35.000)`.
- Enums: `BankSource` (SANTANDER, FALABELLA, MANUAL), `TransactionType` (DEBIT, CREDIT).
- Frontend: Vanilla JS + Tailwind CSS served as static files at `/static/`. No build step.
- File uploads: max 10MB, accept `.csv`, `.xlsx`, `.xls`.
