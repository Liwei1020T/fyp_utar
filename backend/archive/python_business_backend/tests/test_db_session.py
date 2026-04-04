from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db


def test_get_db_yields_a_working_sqlalchemy_session():
    db = next(get_db())

    try:
        assert isinstance(db, Session)
        result = db.execute(text("SELECT 1")).scalar_one()
        assert result == 1
    finally:
        db.close()
