# Legacy Python Business Backend

This directory contains the deprecated FastAPI business backend that previously owned public business APIs, SQLAlchemy models, and Alembic migrations.

It is retained for reference only.

What is archived here:

- `app/` legacy public business API implementation
- `alembic/` legacy SQLAlchemy migration history
- `alembic.ini` legacy Alembic configuration
- `tests/` legacy Python business-backend tests

What is active now:

- `stringsense_backend/` is the active public business backend
- `ai_service/` remains reusable Python AI logic plus an optional standalone compatibility entrypoint
- SQLAlchemy models in `stringsense_backend/db/models.py` plus root `migrations/` are the active schema source of truth

Do not route frontend traffic to anything in this directory.
Do not treat the archived SQLAlchemy/Alembic models as active schema owners.
