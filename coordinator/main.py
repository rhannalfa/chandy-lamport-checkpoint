import os
import time
from coordinator import Coordinator
from db_client import start_checkpoint_session, complete_checkpoint_session

if __name__ == '__main__':
    workers_env = os.getenv('WORKERS', 'worker1:5001,worker2:5001')
    workers = workers_env.split(',')
    
    print("Coordinator nyala! Nunggu worker siap...")
    time.sleep(10) 
    
    # 1. Catat awal sesi di DB
    session_id = start_checkpoint_session(len(workers))
    print(f"Sesi Checkpoint Dimulai: {session_id}")
    
    coord = Coordinator(host='0.0.0.0', port=5000, workers=workers)
    
    # 2. Jalankan algoritma Chandy-Lamport
    print("Memulai broadcast checkpoint...")
    sukses = coord.broadcast_checkpoint()
    
    if sukses:
        # 3. Kalau sukses, update status jadi completed
        complete_checkpoint_session(session_id, len(workers))
        print("=> STATUS: Checkpoint Global BERHASIL & Dicatat ke DB!")
    else:
        print("=> STATUS: Checkpoint Global GAGAL!")
        
    while True:
        time.sleep(60)