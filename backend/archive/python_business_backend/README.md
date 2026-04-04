# Legacy Python Business Backend

This directory contains the deprecated FastAPI business backend that previously owned public business APIs, SQLAlchemy models, and Alembic migrations.

It is retained for reference only.

What is archived here:

- `app/` legacy public business API implementation
- `alembic/` legacy SQLAlchemy migration history
- `alembic.ini` legacy Alembic configuration
- `tests/` legacy Python business-backend tests

What is active now:

- `nest-api/` is the only active public business backend
- `ai_service/` is the only active Python service, and it is AI-only
- Prisma in `nest-api/prisma/schema.prisma` is the active core business schema source of truth

Do not route frontend traffic to anything in this directory.
Do not treat the archived SQLAlchemy/Alembic models as active schema owners.
