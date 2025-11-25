import psycopg2
import os
from typing import Optional
import time
import logging


class DatabaseConnection:
    """Database connection class with retry logic and environment-based configuration."""
    
    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", "db")
        self.database = os.getenv("POSTGRES_DB", "pid_db")
        self.user = os.getenv("POSTGRES_USER", "pid_user")
        self.password = os.getenv("POSTGRES_PASSWORD", "pid_password")
        
    def get_connection(self, max_retries: int = 10, delay: int = 2):
        """Get database connection with retry logic."""
        for attempt in range(max_retries):
            try:
                conn = psycopg2.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                logging.info(f"✅ Koneksi DB berhasil pada percobaan ke-{attempt + 1}")
                return conn
            except psycopg2.OperationalError as e:
                if attempt < max_retries - 1:
                    logging.warning(f"❌ Koneksi DB gagal pada percobaan ke-{attempt + 1}: {e}. Mencoba ulang dalam {delay} detik...")
                    time.sleep(delay)
                else:
                    logging.error(f"❌ Gagal koneksi ke database setelah {max_retries} percobaan: {e}")
                    raise e
        return None