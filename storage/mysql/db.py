import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager

Base = declarative_base()


class DatabaseManager:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
        self.SessionLocal = sessionmaker(bind=self.engine)

    @contextmanager
    def session(self):
        """Context manager that handles session creation and cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self):
        """Get a new session (remember to close it manually)"""
        return self.SessionLocal()


MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_ROOT_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD', 'Secure1234')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'premiumhorsefeeds')

# Initialize the global database manager
db = DatabaseManager(
    f'mysql+pymysql://{MYSQL_USER}:{MYSQL_ROOT_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}'
)
