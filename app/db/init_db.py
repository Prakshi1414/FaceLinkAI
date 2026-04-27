import logging

from app.db.database import Base, engine

# Import models so that Base.metadata knows about them
from app.models import models  

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    logger.info("Dropping all existing tables …")
    #Base.metadata.drop_all(bind=engine)
    logger.info("Creating tables from scratch …")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised successfully.")


if __name__ == "__main__":
    init_db()