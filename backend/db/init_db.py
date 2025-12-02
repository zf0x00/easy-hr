# init_db.py
import duckdb
import os
import time
import portalocker
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "candidates.duckdb")
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")
LOCK_FILE = DB_PATH + ".lock"   # lock file next to DB

# Configurable retry behavior
MAX_WAIT_SECONDS = 20
INITIAL_BACKOFF = 0.05  # 50ms

@contextmanager
def file_lock(path, timeout=None):
    """
    Cross-process exclusive lock using portalocker.
    Yields once the lock is acquired.
    """
    # Ensure lock directory exists
    lock_dir = os.path.dirname(path)
    if lock_dir and not os.path.exists(lock_dir):
        os.makedirs(lock_dir, exist_ok=True)

    fh = open(path, "a+")  # create lock file if missing
    try:
        portalocker.lock(fh, portalocker.LOCK_EX)
        yield
    finally:
        try:
            portalocker.unlock(fh)
        except Exception:
            pass
        fh.close()

def _read_schema():
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        return f.read()

def init_db():
    """
    Safe DB initialization with cross-process locking and retry.
    This will only let one process run the DDL at once.
    """
    # Ensure directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    start = time.time()
    backoff = INITIAL_BACKOFF

    while True:
        try:
            # Acquire the file lock to ensure a single initializer
            with file_lock(LOCK_FILE):
                # Once we hold the lock, open the DB and run schema
                conn = duckdb.connect(DB_PATH)
                try:
                    schema_sql = _read_schema()
                    # Make sure schema.sql is idempotent (use CREATE TABLE IF NOT EXISTS)
                    conn.execute(schema_sql)
                    # Optional: run a simple test query
                    conn.execute("PRAGMA show_progress=false")  # harmless
                finally:
                    conn.close()
                print("Initialized DuckDB at:", DB_PATH)
                return  # success
        except portalocker.exceptions.LockException:
            # couldn't get the lock, fall through to retry
            pass
        except duckdb.Error as e:
            # Common error when DB is temporarily locked; we'll retry
            # If it's an unexpected error, raise after timeout
            last_err = e

        # timeout handling
        elapsed = time.time() - start
        if elapsed >= MAX_WAIT_SECONDS:
            # Give a helpful error after timeout
            raise RuntimeError(
                f"Timed out trying to initialize DuckDB at {DB_PATH} after {MAX_WAIT_SECONDS}s. "
                f"Last error: {locals().get('last_err')}"
            )
        time.sleep(backoff)
        backoff = min(backoff * 2, 1.0)  # exponential backoff (cap 1s)

if __name__ == "__main__":
    init_db()
