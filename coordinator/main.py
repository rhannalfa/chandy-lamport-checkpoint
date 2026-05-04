import socket
import threading
import json
import time
import os
from typing import List, Dict
from db_client import create_checkpoint_session, update_session_status, increment_ack

class Coordinator:
    def __init__(self, host: str, port: int, workers: List[str]):
        """Inisialisasi coordinator dengan daftar worker node."""
        self.host = host
        self.port = port
        self.workers = workers
        self.acks: Dict[str, bool] = {}
        self.lock = threading.Lock()

    def broadcast_checkpoint(self) -> bool:
        """Broadcast sinyal MARKER ke semua worker (Chandy-Lamport)."""
        
        total_nodes = len(self.workers)
        session_id = create_checkpoint_session(total_nodes)
        print(f"[COORDINATOR] Sesi Checkpoint Dimulai dengan ID: {session_id}")

        self.acks = {w: False for w in self.workers}
        
        signal = json.dumps({
            'type': 'MARKER', 
            'session_id': session_id,
            'from': 'coordinator'
        })

        for worker in self.workers:
            host, port = worker.split(':')
            try:
                with socket.create_connection((host, int(port)), timeout=5) as s:
                    s.sendall(signal.encode())
                    
                    response = s.recv(1024)
                    if response:
                        res_data = json.loads(response.decode())
                        if res_data.get('status') == 'ACK':
                            self.receive_ack(worker, session_id)
            except Exception as e:
                print(f'[WARN] Gagal kontak {worker}: {e}')

        deadline = time.time() + 30
        while time.time() < deadline:
            with self.lock:
                if all(self.acks.values()):
                    update_session_status(session_id, 'completed')
                    print("=> STATUS: Checkpoint Global BERHASIL & Dicatat ke DB!")
                    return True
            time.sleep(0.5)
            
        update_session_status(session_id, 'failed')
        print("=> STATUS: Checkpoint Global GAGAL (Timeout)!")
        return False

    def receive_ack(self, worker_id: str, session_id: str):
        """Mencatat konfirmasi (ACK) yang diterima dari worker."""
        with self.lock:
            self.acks[worker_id] = True
            print(f'[ACK] Diterima dari {worker_id}')
            increment_ack(session_id)

def main():
    WORKERS_ENV = os.getenv('WORKERS', 'worker1:5001,worker2:5001,worker3:5001')
    worker_list = WORKERS_ENV.split(',')
    
    print("Coordinator nyala! Nunggu worker siap...")
    time.sleep(5) 
    
    coord = Coordinator('0.0.0.0', 5000, worker_list)
    coord.broadcast_checkpoint()

if __name__ == '__main__':
    main()