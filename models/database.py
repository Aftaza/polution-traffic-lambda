import os
from typing import Optional
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import psycopg2


class DatabaseConnection:
    """Database connection class with retry logic and environment-based configuration using SQLAlchemy."""

    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", "db")
        self.database = os.getenv("POSTGRES_DB", "pid_db")
        self.user = os.getenv("POSTGRES_USER", "pid_user")
        self.password = os.getenv("POSTGRES_PASSWORD", "pid_password")
        self.engine = None
        self._create_engine()

    def _create_engine(self, max_retries: int = 10, delay: int = 2):
        """Create SQLAlchemy engine with retry logic."""
        # PostgreSQL connection string
        connection_string = f"postgresql://{self.user}:{self.password}@{self.host}/{self.database}"

        for attempt in range(max_retries):
            try:
                # Create SQLAlchemy engine with proper connection pooling
                self.engine = create_engine(
                    connection_string,
                    poolclass=QueuePool,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,  # Verify connections before use
                    pool_recycle=3600,    # Recycle connections every hour
                    echo=False           # Set to True for SQL debug logging
                )
                # Test the connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                logging.info(f"✅ SQLAlchemy engine berhasil dibuat pada percobaan ke-{attempt + 1}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logging.warning(f"❌ Gagal membuat SQLAlchemy engine pada percobaan ke-{attempt + 1}: {e}. Mencoba ulang dalam {delay} detik...")
                    time.sleep(delay)
                else:
                    logging.error(f"❌ Gagal membuat SQLAlchemy engine setelah {max_retries} percobaan: {e}")
                    raise e

    def get_connection(self):
        """Get SQLAlchemy connection from the engine."""
        return self.engine.connect() if self.engine else None

    def get_engine(self):
        """Get the SQLAlchemy engine."""
        return self.engine