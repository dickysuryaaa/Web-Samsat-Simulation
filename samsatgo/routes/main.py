from datetime import datetime

from flask import flash, render_template, request, session

from samsatgo.extensions import db
from samsatgo.formatters import rupiah
from samsatgo.models import (
    Fine,
    FineCheckInquiry,
    StnkRenewalApplication,
    TaxCheckInquiry,
    TaxRecord,
    Vehicle,
    VehicleInfoInquiry,
)
from samsatgo.routes.auth import login_required
from samsatgo.services.upload_service import save_uploaded_image


def find_user_vehicle(plate_number):
    return Vehicle.query.filter(
        Vehicle.user_id == session["user_id"],
        Vehicle.plate_number == plate_number,
    ).first()


def frame_matches(vehicle, last_five_digits):
    return bool(vehicle.frame_number) and vehicle.frame_number[-5:] == last_five_digits


def register_main_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/informasi")
    def informasi():
        return render_template("informasi.html")

    @app.route("/cek-pajak", methods=["GET", "POST"])
    @login_required
    def cek_pajak():
        result = None
        if request.method == "POST":
            nrkb = request.form.get("nrkb", "").strip().upper()
            no_rangka = request.form.get("no_rangka", "").strip()
            nik = request.form.get("nik", "").strip()
            vehicle = find_user_vehicle(nrkb)
            inquiry = TaxCheckInquiry(
                user_id=session["user_id"],
                nrkb=nrkb,
                frame_last_five=no_rangka,
                nik=nik,
                result_status="not_found",
            )
            db.session.add(inquiry)

            if not vehicle:
                flash("Data kendaraan tidak ditemukan untuk akun ini.", "error")
            elif not frame_matches(vehicle, no_rangka):
                inquiry.vehicle_id = vehicle.id
                inquiry.result_status = "frame_mismatch"
                flash("Nomor rangka tidak cocok.", "error")
            elif not vehicle.user.nik or nik != vehicle.user.nik:
                inquiry.vehicle_id = vehicle.id
                inquiry.result_status = "nik_mismatch"
                flash("NIK tidak cocok dengan pemilik kendaraan.", "error")
            else:
                inquiry.vehicle_id = vehicle.id
                tax = (
                    TaxRecord.query.filter_by(vehicle_id=vehicle.id)
                    .order_by(TaxRecord.tax_year.desc())
                    .first()
                )
                if tax:
                    inquiry.tax_record_id = tax.id
                    inquiry.result_status = "found"
                    result = {
                        "tax_id": tax.id,
                        "nrkb": vehicle.plate_number,
                        "no_rangka": vehicle.frame_number[-5:] if vehicle.frame_number else "-",
                        "merk": vehicle.brand,
                        "tipe": vehicle.model,
                        "tahun": vehicle.year,
                        "pajak_pokok": rupiah(tax.base_tax),
                        "denda": rupiah(tax.fine_amount),
                        "total": rupiah(tax.total_amount),
                        "jatuh_tempo": tax.due_date.strftime("%d %B %Y") if tax.due_date else "-",
                        "status": "Sudah Bayar" if tax.status == "paid" else "Belum Bayar",
                    }
                else:
                    inquiry.result_status = "tax_not_available"
                    flash("Data pajak kendaraan belum tersedia.", "warning")
            db.session.commit()

        return render_template("cek_pajak.html", result=result)

    @app.route("/pajak-5-tahunan", methods=["GET", "POST"])
    @login_required
    def pajak_5_tahunan():
        step = request.args.get("step", "1")
        result = None
        if request.method == "POST":
            nrkb = request.form.get("nrkb", "").strip().upper()
            no_rangka = request.form.get("no_rangka", "").strip()
            nik = request.form.get("nik", "").strip()
            lokasi = request.form.get("lokasi", "").strip()
            tanggal = request.form.get("tanggal", "").strip()

            vehicle = find_user_vehicle(nrkb)
            if not vehicle:
                flash("Data kendaraan tidak ditemukan untuk akun ini.", "error")
            elif not frame_matches(vehicle, no_rangka):
                flash("Nomor rangka tidak cocok.", "error")
            elif not vehicle.user.nik or nik != vehicle.user.nik:
                flash("NIK tidak cocok dengan pemilik kendaraan.", "error")
            elif not lokasi or not tanggal:
                flash("Lokasi dan tanggal kedatangan wajib diisi.", "error")
            else:
                try:
                    ktp_photo_path = save_uploaded_image(request.files.get("foto_ktp"), "stnk_renewals")
                    stnk_photo_path = save_uploaded_image(request.files.get("foto_stnk"), "stnk_renewals")
                    vehicle_photo_path = save_uploaded_image(request.files.get("foto_kendaraan"), "stnk_renewals")
                    physical_check_photo_path = save_uploaded_image(request.files.get("foto"), "stnk_renewals")
                    if not ktp_photo_path or not stnk_photo_path or not vehicle_photo_path:
                        raise ValueError("Foto KTP, STNK, dan kendaraan wajib diunggah.")
                except ValueError as exc:
                    flash(str(exc), "error")
                    return render_template("pajak_5_tahunan.html", result=None, step="1")

                application = StnkRenewalApplication(
                    user_id=session["user_id"],
                    vehicle_id=vehicle.id,
                    nrkb=nrkb,
                    frame_last_five=no_rangka,
                    nik=nik,
                    location=lokasi,
                    appointment_date=datetime.strptime(tanggal, "%Y-%m-%d").date(),
                    ktp_photo_path=ktp_photo_path,
                    stnk_photo_path=stnk_photo_path,
                    vehicle_photo_path=vehicle_photo_path,
                    physical_check_photo_path=physical_check_photo_path,
                    admin_fee=150000,
                    status="submitted",
                )
                db.session.add(application)
                db.session.commit()

                result = {
                    "id": application.id,
                    "nrkb": vehicle.plate_number,
                    "lokasi": lokasi,
                    "tanggal": tanggal,
                    "admin_fee": rupiah(application.admin_fee),
                }
                step = "2"
        return render_template("pajak_5_tahunan.html", result=result, step=step)

    @app.route("/cek-denda", methods=["GET", "POST"])
    @login_required
    def cek_denda():
        result = None
        if request.method == "POST":
            no_polisi = request.form.get("no_polisi", "").strip().upper()
            no_rangka = request.form.get("no_rangka", "").strip()
            no_mesin = request.form.get("no_mesin", "").strip()
            wilayah = request.form.get("wilayah", "").strip()
            vehicle = find_user_vehicle(no_polisi)
            inquiry = FineCheckInquiry(
                user_id=session["user_id"],
                police_number=no_polisi,
                frame_number_input=no_rangka,
                engine_number_input=no_mesin,
                incident_location=wilayah,
                result_status="not_found",
            )
            db.session.add(inquiry)

            if not vehicle:
                flash("Data kendaraan tidak ditemukan untuk akun ini.", "error")
            elif no_rangka and not frame_matches(vehicle, no_rangka[-5:]):
                inquiry.vehicle_id = vehicle.id
                inquiry.result_status = "frame_mismatch"
                flash("Nomor rangka tidak cocok.", "error")
            elif no_mesin and vehicle.engine_number and no_mesin != vehicle.engine_number:
                inquiry.vehicle_id = vehicle.id
                inquiry.result_status = "engine_mismatch"
                flash("Nomor mesin tidak cocok.", "error")
            else:
                inquiry.vehicle_id = vehicle.id
                fine_query = Fine.query.filter_by(vehicle_id=vehicle.id, status="unpaid")
                if wilayah:
                    fine_query = fine_query.filter(Fine.location == wilayah)
                fine = fine_query.order_by(Fine.violation_date.desc()).first()
                if not fine:
                    inquiry.result_status = "no_active_fine"
                    flash("Tidak ada denda aktif untuk kendaraan ini.", "success")
                else:
                    inquiry.fine_id = fine.id
                    inquiry.result_status = "found"
                    result = {
                        "fine_id": fine.id,
                        "no_polisi": vehicle.plate_number,
                        "no_rangka": vehicle.frame_number or no_rangka,
                        "no_mesin": vehicle.engine_number or no_mesin,
                        "lokasi": fine.location or wilayah or "-",
                        "pelanggaran": fine.description,
                        "tanggal": fine.violation_date.strftime("%d %B %Y") if fine.violation_date else "-",
                        "denda": rupiah(fine.amount),
                        "status": "Belum Dibayar",
                    }
            db.session.commit()

        return render_template("cek_denda.html", result=result)

    @app.route("/cek-tilang")
    @login_required
    def cek_tilang():
        fine = (
            Fine.query.join(Vehicle)
            .filter(Vehicle.user_id == session["user_id"], Fine.status == "unpaid")
            .first()
        )
        data = {
            "no_polisi": fine.vehicle.plate_number if fine else request.args.get("no_polisi", "-"),
            "no_rangka": fine.vehicle.frame_number if fine else "-",
            "no_mesin": fine.vehicle.engine_number if fine else "-",
            "lokasi": fine.location if fine else "-",
            "pelanggaran": fine.description if fine else "Tidak ada pelanggaran aktif",
            "tanggal": fine.violation_date.strftime("%d %B %Y") if fine and fine.violation_date else "-",
            "denda": rupiah(fine.amount) if fine else rupiah(0),
        }
        return render_template("cek_tilang.html", data=data)

    @app.route("/informasi-kendaraan", methods=["GET", "POST"])
    @login_required
    def informasi_kendaraan():
        result = None
        if request.method == "POST":
            no_polisi = request.form.get("no_polisi", "").strip().upper()
            nrkb = request.form.get("nrkb", "").strip().upper()
            no_rangka = request.form.get("no_rangka", "").strip()
            nik = request.form.get("nik", "").strip()
            plate_number = nrkb or no_polisi
            vehicle = find_user_vehicle(plate_number)
            inquiry = VehicleInfoInquiry(
                user_id=session["user_id"],
                police_number=no_polisi,
                nrkb=nrkb,
                frame_last_five=no_rangka,
                nik=nik,
                result_status="not_found",
            )
            db.session.add(inquiry)

            if not vehicle:
                flash("Data kendaraan tidak ditemukan untuk akun ini.", "error")
                step = "1"
            elif no_polisi and no_polisi != vehicle.plate_number:
                inquiry.vehicle_id = vehicle.id
                inquiry.result_status = "plate_mismatch"
                flash("No. Polisi tidak cocok dengan NRKB.", "error")
                step = "1"
            elif not frame_matches(vehicle, no_rangka):
                inquiry.vehicle_id = vehicle.id
                inquiry.result_status = "frame_mismatch"
                flash("Nomor rangka tidak cocok.", "error")
                step = "1"
            elif not vehicle.user.nik or nik != vehicle.user.nik:
                inquiry.vehicle_id = vehicle.id
                inquiry.result_status = "nik_mismatch"
                flash("NIK tidak cocok dengan pemilik kendaraan.", "error")
                step = "1"
            else:
                inquiry.vehicle_id = vehicle.id
                inquiry.result_status = "found"
                step = "2"
                result = {
                    "no_polisi": vehicle.plate_number,
                    "nrkb": vehicle.plate_number,
                    "no_rangka": vehicle.frame_number or no_rangka,
                    "nik": vehicle.user.nik or nik,
                    "merk": vehicle.brand,
                    "tipe": vehicle.model,
                    "tahun": vehicle.year,
                    "warna": vehicle.color,
                }
            db.session.commit()
        else:
            step = request.args.get("step", "1")
        return render_template("informasi_kendaraan.html", result=result, step=step)
