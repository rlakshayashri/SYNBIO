from sqlalchemy.orm import Session

from app.core.logging import logger


def init_db(db: Session) -> None:
    """Initializes the database with seed or startup records if required.

    Migrations are managed exclusively via Alembic.
    """
    logger.info("Initializing database session...")
