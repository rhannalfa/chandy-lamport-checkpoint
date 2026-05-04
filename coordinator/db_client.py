import os
import psycopg2
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
    """Mengelola context manager untuk koneksi database."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ==========================================
# FUNGSI UNTUK COORDINATOR
# ==========================================

def create_checkpoint_session(total_nodes: int, trigger_type: str = 'manual') -> str:
    """Inisiasi sesi koordinasi global di tabel checkpoint_sessions."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO checkpoint_sessions (total_nodes, trigger_type, global_status, acked_nodes)
                VALUES (%s, %s, 'in_progress', 0)
                RETURNING session_id""", (total_nodes, trigger_type))
            return str(cur.fetchone()[0])

def update_session_status(session_id: str, status: str):
    """Update status sesi global checkpoint."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            if status == 'completed':
                cur.execute("""
                    UPDATE checkpoint_sessions 
                    SET global_status = %s, completed_at = NOW() 
                    WHERE session_id = %s""", (status, session_id))
            else:
                cur.execute("""
                    UPDATE checkpoint_sessions 
                    SET global_status = %s 
                    WHERE session_id = %s""", (status, session_id))

def increment_ack(session_id: str):
    """Nambah jumlah ACK yang masuk ke DB secara real-time."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE checkpoint_sessions 
                SET acked_nodes = acked_nodes + 1 
                WHERE session_id = %s""", (session_id,))

# ==========================================
# FUNGSI UNTUK WORKER
# ==========================================

def register_checkpoint(node_id: str, session_id: str, seq: int, path: str, size_kb: int, checksum: str) -> str:
    """Mencatat metadata file checkpoint ke tabel checkpoints[cite: 131]."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO checkpoints
                (node_id, session_id, sequence_number, file_path, file_size_kb, checksum, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'valid')
                RETURNING checkpoint_id""",
                (node_id, session_id, seq, path, size_kb, checksum))
            return str(cur.fetchone()[0])

def get_latest_valid_checkpoints() -> list:
    """Ambil checkpoint valid terbaru per node untuk proses recovery."""
    query = """
    SELECT DISTINCT ON (c.node_id)
        c.checkpoint_id, c.node_id, n.node_name, c.file_path, c.sequence_number, c.created_at
    FROM checkpoints c
    JOIN nodes n ON n.node_id = c.node_id
    WHERE c.status = 'valid'
    ORDER BY c.node_id, c.sequence_number DESC
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()