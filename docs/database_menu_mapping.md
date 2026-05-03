# Pemetaan Database Sesuai Menu SamsatGo

Dokumen ini menjelaskan tabel yang dipakai oleh setiap menu dan field form yang disimpan.

## 1. Cek Pajak Kendaraan

Form:

- `nrkb`
- `no_rangka` atau 5 digit terakhir nomor rangka
- `nik`

Tabel input menu:

- `tax_check_inquiries`

Kolom penting:

- `user_id`
- `vehicle_id`
- `tax_record_id`
- `nrkb`
- `frame_last_five`
- `nik`
- `result_status`
- `created_at`

Tabel master yang dibaca:

- `vehicles`
- `tax_records`
- `users`

## 2. Perpanjang STNK 5 Tahunan

Form:

- `nrkb`
- `no_rangka`
- `nik`
- `foto_ktp`
- `foto_stnk`
- `foto_kendaraan`
- `foto`
- `lokasi`
- `tanggal`

Tabel input menu:

- `stnk_renewal_applications`

Kolom penting:

- `user_id`
- `vehicle_id`
- `nrkb`
- `frame_last_five`
- `nik`
- `location`
- `appointment_date`
- `ktp_photo_path`
- `stnk_photo_path`
- `vehicle_photo_path`
- `physical_check_photo_path`
- `admin_fee`
- `status`
- `created_at`

File upload disimpan di:

- `static/uploads/stnk_renewals/`

## 3. Cek Status Pelanggaran & Denda

Form:

- `no_polisi`
- `no_rangka`
- `no_mesin`
- `wilayah`

Tabel input menu:

- `fine_check_inquiries`

Kolom penting:

- `user_id`
- `vehicle_id`
- `fine_id`
- `police_number`
- `frame_number_input`
- `engine_number_input`
- `incident_location`
- `result_status`
- `created_at`

Tabel master yang dibaca:

- `vehicles`
- `fines`

## 4. Informasi Kendaraan

Form:

- `no_polisi`
- `nrkb`
- `no_rangka`
- `nik`

Tabel input menu:

- `vehicle_info_inquiries`

Kolom penting:

- `user_id`
- `vehicle_id`
- `police_number`
- `nrkb`
- `frame_last_five`
- `nik`
- `result_status`
- `created_at`

Tabel master yang dibaca:

- `vehicles`
- `users`

## 5. Pembayaran

Tabel transaksi:

- `transactions`

Relasi pembayaran:

- `tax_record_id` untuk pajak kendaraan
- `fine_id` untuk denda/tilang
- `stnk_renewal_application_id` untuk STNK 5 tahunan

Kolom penting:

- `order_id`
- `gross_amount`
- `snap_token`
- `snap_redirect_url`
- `payment_type`
- `transaction_status`
- `fraud_status`
- `midtrans_transaction_id`
- `paid_at`
- `raw_response`

