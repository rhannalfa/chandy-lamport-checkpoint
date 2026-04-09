import pickle
import socket
import threading
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CheckpointData:
    node_id: str
    sequence_number: int
    state: dict
    timestamp: str
    checksum: str

class CheckpointManager:
    def __init__(self, node_id: str, storage_path: str):
        self.node_id = node_id
        self.storage_path = Path(storage_path)
        self.sequence = 0
        self.logger = logging.getLogger(__name__)

    def save_checkpoint(self, state: dict) -> str:
        """Simpan state ke file .ckpt dan return path-nya."""
        self.sequence += 1
        serialized = pickle.dumps(state)
        checksum = hashlib.sha256(serialized).hexdigest()

        ckpt = CheckpointData(
            node_id=self.node_id,
            sequence_number=self.sequence,
            state=state,
            timestamp=datetime.utcnow().isoformat(),
            checksum=checksum
        )

        file_path = self.storage_path / f"{self.node_id}_ckpt_{self.sequence}.pkl"
        with open(file_path, 'wb') as f:
            pickle.dump(ckpt, f)

        self.logger.info(f"Checkpoint {self.sequence} saved: {file_path}")
        return str(file_path)

    def load_checkpoint(self, file_path: str) -> dict:
        """Load state dari file checkpoint terakhir."""
        with open(file_path, 'rb') as f:
            ckpt: CheckpointData = pickle.load(f)
            
        # Verifikasi integritas
        serialized = pickle.dumps(ckpt.state)
        checksum = hashlib.sha256(serialized).hexdigest()
        if checksum != ckpt.checksum:
            raise ValueError('Checkpoint file corrupt!')
            
        return ckpt.state