# Distributed Checkpoint Chandy-Lamport 🚀

Implementasi algoritma **Chandy-Lamport** untuk merekam *global snapshot* (checkpoint) pada sistem *terdistribusi* secara asinkron. Sistem ini memungkinkan pencatatan *state* dari banyak *node* secara bersamaan tanpa perlu menghentikan proses atau transaksi yang sedang berlangsung (*zero downtime*).

## 🏗️ Arsitektur Sistem

Proyek ini dikembangkan menggunakan arsitektur *microservices* dan seluruhnya di-*deploy* di atas **Docker**:
- **Coordinator (Python):** Bertanggung jawab menginisiasi sesi *checkpoint* dan melakukan *broadcast* sinyal `MARKER` ke seluruh *node*.
- **Worker Node (Python):** 2 instans *worker* yang menerima sinyal, menyimpan *state* lokal secara mandiri, dan mengirimkan `ACK` kembali ke *coordinator*.
- **Database (PostgreSQL):** Tersentralisasi untuk mencatat riwayat sesi *checkpoint* beserta metrik waktu eksekusinya.

## 🛠️ Teknologi yang Digunakan
- **Bahasa Pemrograman:** Python 3.11
- **Containerization:** Docker & Docker Compose
- **Database:** PostgreSQL 15
- **Komunikasi:** TCP Socket & JSON

## 🚀 Cara Menjalankan

1. **Clone repositori ini**
```bash
   git clone https://github.com/rhannalfa/chandy-lamport-checkpoint.git
   cd chandy-lamport-checkpoint
```

2. **Jalankan seluruh container**
```bash
   docker compose up -d --build
```

3. **Tunggu database siap, lalu jalankan ulang Coordinator**
   Karena PostgreSQL memerlukan waktu inisialisasi di awal, *restart coordinator* agar proses *broadcast* segera dimulai:
```bash
   docker compose restart coordinator
```

4. **Pantau proses checkpoint secara real-time**
```bash
   docker compose logs -f coordinator
```
   Tunggu hingga log berikut muncul:
   `=> STATUS: Checkpoint Global BERHASIL & Dicatat ke DB!`

## 📊 Hasil Evaluasi & Performa

Berdasarkan pengujian dengan topologi 1 *Coordinator* dan 2 *Worker*, algoritma sinkronisasi ini berjalan dengan performa yang sangat baik.

Untuk melihat durasi total eksekusi dalam milidetik, jalankan *query* berikut di terminal:
```bash
docker compose exec postgres psql -U ckpt_user -d checkpoint_db -c \
"SELECT session_id, total_nodes, acked_nodes, global_status, \
EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000 AS durasi_ms \
FROM checkpoint_sessions WHERE global_status = 'completed';"
```

Sistem berhasil melakukan *global snapshot* dengan rata-rata durasi **494,53 milidetik** (kurang dari 0,5 detik).

## 📂 Struktur Direktori

| Direktori/File | Keterangan |
|---|---|
| `/coordinator` | Skrip dan Dockerfile untuk inisiator |
| `/worker` | Skrip klien dan Dockerfile untuk *node* |
| `/sql` | Skrip `init.sql` untuk migrasi tabel PostgreSQL secara otomatis |
| `docker-compose.yml` | Konfigurasi orkestrasi *container*, *network*, dan *volume* |
