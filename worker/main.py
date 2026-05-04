import os
import socket
import json
import hashlib
from checkpoint_manager import CheckpointManager
from db_client import get_conn, register_checkpoint

NODE_NAME = os.getenv('NODE_ID', 'worker1')
PORT = 5001

def get_or_create_node_id(node_name):
    """Daftarin node ke DB buat dapet UUID (karena wajib buat relasi tabel)"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Cek apakah node udah ada
            cur.execute("SELECT node_id FROM nodes WHERE node_name = %s", (node_name,))
            res = cur.fetchone()
            if res: return res[0]
            
            # Kalau belum, insert baru
            ip = socket.gethostbyname(socket.gethostname())
            cur.execute(
                "INSERT INTO nodes (node_name, ip_address, role) VALUES (%s, %s, 'worker') RETURNING node_id", 
                (node_name, ip)
            )
            return cur.fetchone()[0]

def generate_sha256_checksum(file_path):
    """Fungsi pembaca blok file untuk hitung checksum sesuai paper"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Baca file per 4KB biar aman di memori
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    print(f"[{NODE_NAME}] Worker nyala! Registrasi ke database dulu...")
    node_uuid = get_or_create_node_id(NODE_NAME)
    print(f"[{NODE_NAME}] Sukses dapet UUID: {node_uuid}")
    
    # Manager untuk simpan file .ckpt ke folder shared
    ckpt_manager = CheckpointManager(node_id=NODE_NAME, storage_path='/mnt/checkpoints')
    
    # Bikin socket server untuk nunggu sinyal coordinator
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', PORT))
    server.listen(5)
    print(f"[{NODE_NAME}] Nunggu sinyal MARKER dari coordinator di port {PORT}...")
    
    while True:
        conn, addr = server.accept()
        with conn:
            data = conn.recv(1024)
            if not data: continue
            
            try:
                msg = json.loads(data.decode())
                if msg.get('type') == 'MARKER':
                    session_id = msg.get('session_id') # Tangkap session_id dari coordinator
                    print(f"[{NODE_NAME}] Wih, dapet MARKER untuk sesi {session_id}! Mulai proses...")
                    
                    # 1. Simulasi data aplikasi yang lagi jalan
                    state = {'task': 'hitung_data_berat', 'progress': 85}
                    
                    # 2. Simpan file .ckpt
                    file_path = ckpt_manager.save_checkpoint(state)
                    
                    # 3. Hitung ukuran file dan checksum dari file aslinya
                    file_size_bytes = os.path.getsize(file_path)
                    size_kb = max(1, int(file_size_bytes / 1024)) # Minimal 1 KB biar gak 0 di DB
                    checksum = generate_sha256_checksum(file_path)
                    
                    # 4. Catat histori checkpoint ke Database
                    db_id = register_checkpoint(
                        node_id=node_uuid,
                        session_id=session_id, # Masukin ID dari MARKER
                        seq=ckpt_manager.sequence,
                        path=file_path,
                        size_kb=size_kb,
                        checksum=checksum
                    )
                    print(f"[{NODE_NAME}] Checkpoint aman! Masuk DB dengan ID: {db_id}")
                    
                    # Kirim balasan ke coordinator
                    conn.sendall(json.dumps({'status': 'ACK', 'node': NODE_NAME}).encode())
            except Exception as e:
                print(f"[{NODE_NAME}] Ada error: {e}")

if __name__ == '__main__':
    main()