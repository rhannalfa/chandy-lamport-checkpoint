import psycopg2
import os
from contextlib import contextmanager

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'dbname': os.getenv('DB_NAME', 'checkpoint_db'),
    'user': os.getenv('DB_USER', 'ckpt_user'),
    'password': os.getenv('DB_PASSWORD', 'secret'),
}

@contextmanager
def get_conn():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def register_checkpoint(node_id: str, session_id: str,
                        seq: int, path: str, size_kb: int,
                        checksum: str) -> str:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO checkpoints
                (node_id, session_id, sequence_number,
                file_path, file_size_kb, checksum)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING checkpoint_id""",
                (node_id, session_id, seq, path, size_kb, checksum))
            return cur.fetchone()[0]

def get_latest_valid_checkpoints() -> list:
    """Ambil checkpoint valid terbaru per node untuk proses recovery."""
    query = """
    SELECT DISTINCT ON (c.node_id)
        c.checkpoint_id,
        c.node_id,
        n.node_name,
        c.file_path,
        c.sequence_number,
        c.created_at
    FROM   checkpoints c
    JOIN   nodes n ON n.node_id = c.node_id
    WHERE  c.status = 'valid'
    ORDER  BY c.node_id, c.sequence_number DESC
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()