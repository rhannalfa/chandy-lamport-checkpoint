import socket
import threading
import json
import time
from typing import List, Dict

class Coordinator:
    def __init__(self, host: str, port: int, workers: List[str]):
        """Inisialisasi coordinator dengan daftar worker node [cite: 97-100]."""
        self.host = host
        self.port = port
        self.workers = workers   # Format: ['worker1:5001', 'worker2:5001']
        self.acks: Dict[str, bool] = {}
        self.lock = threading.Lock()

    def broadcast_checkpoint(self) -> bool:
        """Broadcast sinyal MARKER ke semua worker (Chandy-Lamport) [cite: 103-104]."""
        # Reset semua status ACK jadi False [cite: 105]
        self.acks = {w: False for w in self.workers}
        signal = json.dumps({'type': 'MARKER', 'from': 'coordinator'})

        for worker in self.workers:
            host, port = worker.split(':')
            try:
                # Bikin koneksi dan kirim sinyal ke tiap worker [cite: 110-111]
                with socket.create_connection((host, int(port)), timeout=5) as s:
                    s.sendall(signal.encode())
                    
                    # Tunggu balasan ACK langsung dari worker setelah mereka simpen state
                    response = s.recv(1024)
                    if response:
                        res_data = json.loads(response.decode())
                        if res_data.get('status') == 'ACK':
                            self.receive_ack(worker)
            except Exception as e:
                print(f'[WARN] Gagal kontak {worker}: {e}')

        # BAGIAN KRUSIAL: Tunggu semua ACK terkumpul (timeout 30 detik) 
        deadline = time.time() + 30
        while time.time() < deadline:
            with self.lock:
                # Kalau semua worker sudah kirim ACK, anggap sukses [cite: 118-119]
                if all(self.acks.values()):
                    return True
            time.sleep(0.5) # Kasih nafas biar nggak makan CPU [cite: 120]
            
        return False  # Timeout tercapai tapi ada node belum lapor [cite: 121]

    def receive_ack(self, worker_id: str):
        """Mencatat konfirmasi (ACK) yang diterima dari worker [cite: 122-126]."""
        with self.lock:
            self.acks[worker_id] = True
            print(f'[ACK] Diterima dari {worker_id} [cite: 126]')