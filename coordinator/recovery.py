import pickle
from dataclasses import dataclass
from db_client import get_latest_valid_checkpoints


def run_recovery():
    print("=== MEMULAI PROSES RECOVERY ===")
    print("Mencari checkpoint valid terakhir di database...")
    
    # Ambil data recovery dari fungsi yang udah kita buat di db_client.py
    checkpoints = get_latest_valid_checkpoints()
    
    if not checkpoints:
        print("Yah, tidak ada data checkpoint yang ditemukan!")
        return

    print(f"Ditemukan {len(checkpoints)} node dengan checkpoint valid.\n")
    
    for ckpt in checkpoints:
        # Urutan index dari query: checkpoint_id, node_id, node_name, file_path, sequence_number, created_at
        node_name = ckpt[2]
        file_path = ckpt[3]
        created_at = ckpt[5]
        
        print(f"-> Memulihkan Node: {node_name}")
        print(f"   Waktu Checkpoint: {created_at}")
        
        # Coba buka file fisiknya dari shared volume
        try:
            with open(file_path, 'rb') as f:
                ckpt_data = pickle.load(f)
                
            state = ckpt_data.state
            print(f"   [SUKSES] Data state dikembalikan: {state}\n")
        except Exception as e:
            print(f"   [GAGAL] File nggak kebaca: {e}\n")

if __name__ == '__main__':
    run_recovery()