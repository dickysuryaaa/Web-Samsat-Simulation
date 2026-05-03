# SamsatGo

SamsatGo adalah mock e-Government berbasis Flask untuk layanan pajak kendaraan, denda/tilang, perpanjang STNK 5 tahunan (upload berkas), dan pembayaran (Midtrans Snap atau mode demo).

## Stack

- Python Flask
- SQLAlchemy ORM
- Flask-Migrate / Alembic
- MySQL via PyMySQL
- Werkzeug password hashing
- Flask-WTF CSRF protection
- Midtrans Snap API
- Jinja2 + Tailwind CDN

## Struktur

```text
.
├── app.py
├── config.py
├── requirements.txt
├── migrations/
├── samsatgo/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   ├── formatters.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── main.py
│   │   └── payment.py
│   └── services/
│       ├── midtrans_service.py
│       └── upload_service.py
├── docs/
│   └── menu_queries.sql
├── templates/
└── static/
```

## Setup

## Menjalankan Dari Laptop Baru Menyala (Cold Start)

Urutan ini diasumsikan dari kondisi: laptop baru dinyalakan, belum ada server yang berjalan.

1. Jalankan MySQL (Laragon):

- Buka Laragon
- Klik `Start All`
- Pastikan MySQL running di port `3306`

2. Masuk ke folder project:

```bash
cd C:\Users\MSI\Documents\pens\web_samsat-main
```

3. (Opsional tapi direkomendasikan) Aktifkan virtualenv:

```bash
.\venv\Scripts\activate
```

4. Install dependency:

```bash
python -m pip install -r requirements.txt
```

5. Siapkan konfigurasi environment:

- Pastikan file `.env` ada (repo ini meng-include `.env` untuk demo lokal).
- Kalau ingin pakai Midtrans Snap asli: isi `MIDTRANS_SERVER_KEY` dan `MIDTRANS_CLIENT_KEY` lalu set `PAYMENT_DEMO_MODE=false`.

6. Setup database (MySQL) dengan migration:

```bash
python -m flask --app app.py db upgrade
```

7. Isi data demo (user + kendaraan + pajak + denda):

```bash
python -m flask --app app.py seed
```

8. Jalankan aplikasi:

```bash
python app.py
```

Akses:

```text
http://127.0.0.1:5000
```

## Database

Aplikasi default memakai MySQL lokal (Laragon) sesuai `.env`:

```env
DATABASE_URL=mysql+pymysql://root:@localhost/samsatgo_flask
```

Untuk memudahkan upload ke GitHub dan pemakaian di laptop lain, dump database MySQL sudah dilampirkan:

- `db/samsatgo_flask.sql`

### Import Database Dari Dump

1. Pastikan MySQL sudah running.
2. Buat database kosong:

```sql
CREATE DATABASE samsatgo_flask CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Import dump:

```bash
mysql -uroot samsatgo_flask < db\samsatgo_flask.sql
```

Catatan: di sebagian environment Windows, command `mysql` tidak ada di PATH. Kalau memakai Laragon, gunakan binary ini:

```bash
"C:\laragon\bin\mysql\mysql-8.4.3-winx64\bin\mysql.exe" -uroot samsatgo_flask < db\samsatgo_flask.sql
```

## Mode Pembayaran

- `PAYMENT_DEMO_MODE=true`: tombol bayar akan langsung menandai tagihan sebagai lunas (tanpa Midtrans).
- `PAYMENT_DEMO_MODE=false`: pembayaran memakai Midtrans Snap, butuh key valid di `.env`.

## Data Uji

Login demo setelah seed:

```text
email: user@example.com
password: password123
```

Data demo kendaraan:

```text
NRKB: AG 1234 RFS
5 digit akhir rangka: 98765
NIK: 3276010101010001
No. Mesin: 98765
Wilayah denda: Surabaya
```

## Dokumen Tambahan

- Query SQL referensi: `docs/menu_queries.sql`
- Pemetaan form -> tabel: `docs/database_menu_mapping.md`

## Catatan GitHub

- `.env` berisi konfigurasi lokal dan secret; untuk repo publik sebaiknya gunakan `.env.example` dan jangan commit `.env`.
- Folder `static/uploads/` sebaiknya tidak di-commit (isi upload user).

## Midtrans

Endpoint pembuatan transaksi:

- `POST /payments/tax/<tax_id>/create`
- `POST /payments/fine/<fine_id>/create`
- `POST /payments/stnk/<application_id>/create`

Webhook Midtrans:

```text
POST /payments/midtrans/notification
```

Untuk development lokal, expose aplikasi memakai tunnel seperti ngrok lalu masukkan URL webhook di dashboard Midtrans.
