import psycopg2
import os
import time

# PERUBAHAN DI SINI: max_retries ditingkatkan dari 5 menjadi 10
def get_db_connection(max_retries=10, delay=2):
    """Mengambil koneksi DB dari Environment Variables dengan retry logic."""
    host = os.getenv("POSTGRES_HOST", "db")
    database = os.getenv("POSTGRES_DB", "pid_db")
    user = os.getenv("POSTGRES_USER", "pid_user")
    password = os.getenv("POSTGRES_PASSWORD", "pid_password")
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password
            )
            print(f"✅ Koneksi DB berhasil pada percobaan ke-{attempt + 1}")
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                # Menambahkan pesan peringatan untuk debugging
                print(f"❌ Koneksi DB gagal pada percobaan ke-{attempt + 1}: {e}. Mencoba ulang dalam {delay} detik...")
                time.sleep(delay)
            else:
                # Melemparkan error hanya setelah semua percobaan gagal
                raise e 
    return None