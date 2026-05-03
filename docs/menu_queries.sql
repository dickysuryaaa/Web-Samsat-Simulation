-- Query referensi SamsatGo.
-- Gunakan parameter sesuai input Flask, contoh: :user_id, :nrkb, :nik.

-- 1. Cek Pajak Kendaraan
INSERT INTO tax_check_inquiries (
  user_id,
  vehicle_id,
  tax_record_id,
  nrkb,
  frame_last_five,
  nik,
  result_status,
  created_at
) VALUES (
  :user_id,
  :vehicle_id,
  :tax_record_id,
  :nrkb,
  :last_frame_digits,
  :nik,
  :result_status,
  NOW()
);

SELECT
  v.id AS vehicle_id,
  v.plate_number,
  v.frame_number,
  v.brand,
  v.model,
  v.year,
  tr.id AS tax_record_id,
  tr.tax_year,
  tr.base_tax,
  tr.fine_amount,
  tr.total_amount,
  tr.due_date,
  tr.status
FROM vehicles v
JOIN users u ON u.id = v.user_id
JOIN tax_records tr ON tr.vehicle_id = v.id
WHERE v.user_id = :user_id
  AND v.plate_number = :nrkb
  AND RIGHT(v.frame_number, 5) = :last_frame_digits
  AND u.nik = :nik
ORDER BY tr.tax_year DESC
LIMIT 1;

-- 2. Perpanjang STNK 5 Tahunan - validasi kendaraan
SELECT v.id, v.plate_number, v.frame_number, u.nik
FROM vehicles v
JOIN users u ON u.id = v.user_id
WHERE v.user_id = :user_id
  AND v.plate_number = :nrkb
  AND RIGHT(v.frame_number, 5) = :last_frame_digits
  AND u.nik = :nik
LIMIT 1;

-- 2. Perpanjang STNK 5 Tahunan - insert permohonan
INSERT INTO stnk_renewal_applications (
  user_id,
  vehicle_id,
  location,
  appointment_date,
  ktp_photo_path,
  stnk_photo_path,
  vehicle_photo_path,
  physical_check_photo_path,
  admin_fee,
  status,
  created_at,
  updated_at
) VALUES (
  :user_id,
  :vehicle_id,
  :location,
  :appointment_date,
  :ktp_photo_path,
  :stnk_photo_path,
  :vehicle_photo_path,
  :physical_check_photo_path,
  150000,
  'submitted',
  NOW(),
  NOW()
);

-- 3. Cek Status Pelanggaran & Denda
INSERT INTO fine_check_inquiries (
  user_id,
  vehicle_id,
  fine_id,
  police_number,
  frame_number_input,
  engine_number_input,
  incident_location,
  result_status,
  created_at
) VALUES (
  :user_id,
  :vehicle_id,
  :fine_id,
  :plate_number,
  :frame_number_input,
  :engine_number,
  :location,
  :result_status,
  NOW()
);

SELECT
  f.id AS fine_id,
  v.plate_number,
  v.frame_number,
  v.engine_number,
  f.violation_code,
  f.description,
  f.location,
  f.amount,
  f.violation_date,
  f.status
FROM fines f
JOIN vehicles v ON v.id = f.vehicle_id
WHERE v.user_id = :user_id
  AND v.plate_number = :plate_number
  AND RIGHT(v.frame_number, 5) = :last_frame_digits
  AND (:engine_number IS NULL OR v.engine_number = :engine_number)
  AND (:location IS NULL OR f.location = :location)
  AND f.status = 'unpaid'
ORDER BY f.violation_date DESC
LIMIT 1;

-- 4. Informasi Kendaraan
INSERT INTO vehicle_info_inquiries (
  user_id,
  vehicle_id,
  police_number,
  nrkb,
  frame_last_five,
  nik,
  result_status,
  created_at
) VALUES (
  :user_id,
  :vehicle_id,
  :police_number,
  :nrkb,
  :last_frame_digits,
  :nik,
  :result_status,
  NOW()
);

SELECT
  v.id,
  v.plate_number,
  v.owner_name,
  v.brand,
  v.model,
  v.year,
  v.color,
  v.frame_number,
  v.engine_number,
  v.stnk_number,
  u.nik
FROM vehicles v
JOIN users u ON u.id = v.user_id
WHERE v.user_id = :user_id
  AND v.plate_number = :nrkb
  AND RIGHT(v.frame_number, 5) = :last_frame_digits
  AND u.nik = :nik
LIMIT 1;

-- 5. Pembayaran - tagihan pajak
SELECT tr.*
FROM tax_records tr
JOIN vehicles v ON v.id = tr.vehicle_id
WHERE v.user_id = :user_id
  AND tr.status = 'unpaid';

-- 5. Pembayaran - denda
SELECT f.*
FROM fines f
JOIN vehicles v ON v.id = f.vehicle_id
WHERE v.user_id = :user_id
  AND f.status = 'unpaid';

-- 5. Pembayaran - permohonan STNK
SELECT *
FROM stnk_renewal_applications
WHERE user_id = :user_id
  AND status = 'submitted';
