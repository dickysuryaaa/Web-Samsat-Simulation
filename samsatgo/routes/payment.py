from datetime import datetime
from uuid import uuid4

from flask import current_app, jsonify, render_template, request, session

from samsatgo.extensions import csrf, db
from samsatgo.models import Fine, StnkRenewalApplication, TaxRecord, Transaction, Vehicle
from samsatgo.routes.auth import login_required
from samsatgo.services.midtrans_service import get_core_client, get_snap_client


def register_payment_routes(app):
    def should_use_demo_payment():
        return current_app.config["PAYMENT_DEMO_MODE"] and not current_app.config["MIDTRANS_SERVER_KEY"]

    def mark_transaction_paid(trx):
        trx.transaction_status = "settlement"
        trx.payment_type = "demo"
        trx.paid_at = datetime.utcnow()
        if trx.tax_record:
            trx.tax_record.status = "paid"
            trx.tax_record.paid_at = trx.paid_at
        if trx.fine:
            trx.fine.status = "paid"
        if trx.stnk_renewal_application:
            trx.stnk_renewal_application.status = "paid"

    @app.route("/pembayaran")
    @login_required
    def pembayaran():
        tax_records = (
            TaxRecord.query.join(Vehicle)
            .filter(Vehicle.user_id == session["user_id"], TaxRecord.status == "unpaid")
            .order_by(TaxRecord.tax_year.desc())
            .all()
        )
        fines = (
            Fine.query.join(Vehicle)
            .filter(Vehicle.user_id == session["user_id"], Fine.status == "unpaid")
            .order_by(Fine.violation_date.desc())
            .all()
        )
        stnk_applications = (
            StnkRenewalApplication.query.filter_by(user_id=session["user_id"], status="submitted")
            .order_by(StnkRenewalApplication.created_at.desc())
            .all()
        )
        return render_template(
            "pembayaran.html",
            tax_records=tax_records,
            fines=fines,
            stnk_applications=stnk_applications,
            midtrans_client_key=current_app.config["MIDTRANS_CLIENT_KEY"],
            is_midtrans_configured=bool(current_app.config["MIDTRANS_SERVER_KEY"]),
            payment_demo_mode=should_use_demo_payment(),
        )

    @app.route("/payments/tax/<int:tax_id>/create", methods=["POST"])
    @login_required
    def create_tax_payment(tax_id):
        tax = (
            TaxRecord.query.join(Vehicle)
            .filter(TaxRecord.id == tax_id, Vehicle.user_id == session["user_id"])
            .first_or_404()
        )

        if tax.status == "paid":
            return jsonify({"message": "Tagihan sudah dibayar."}), 400

        order_id = f"SAMSATGO-TAX-{tax.id}-{uuid4().hex[:10]}"
        trx = Transaction(
            user_id=session["user_id"],
            tax_record_id=tax.id,
            order_id=order_id,
            gross_amount=tax.total_amount,
            transaction_status="created",
        )
        db.session.add(trx)
        db.session.flush()

        if should_use_demo_payment():
            mark_transaction_paid(trx)
            db.session.commit()
            return jsonify({"order_id": trx.order_id, "demo_paid": True})

        payload = {
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": tax.total_amount,
            },
            "customer_details": {
                "first_name": session["user"]["name"],
                "email": session["user"]["email"],
            },
            "item_details": [
                {
                    "id": f"TAX-{tax.id}",
                    "price": tax.total_amount,
                    "quantity": 1,
                    "name": f"Pajak {tax.vehicle.plate_number} Tahun {tax.tax_year}",
                }
            ],
            "credit_card": {"secure": True},
        }

        midtrans_response = get_snap_client().create_transaction(payload)
        trx.snap_token = midtrans_response["token"]
        trx.snap_redirect_url = midtrans_response["redirect_url"]
        trx.raw_response = midtrans_response
        db.session.commit()

        return jsonify(
            {
                "order_id": trx.order_id,
                "snap_token": trx.snap_token,
                "redirect_url": trx.snap_redirect_url,
            }
        )

    @app.route("/payments/stnk/<int:application_id>/create", methods=["POST"])
    @login_required
    def create_stnk_payment(application_id):
        application = StnkRenewalApplication.query.filter_by(
            id=application_id,
            user_id=session["user_id"],
        ).first_or_404()

        if application.status == "paid":
            return jsonify({"message": "Permohonan STNK sudah dibayar."}), 400

        order_id = f"SAMSATGO-STNK-{application.id}-{uuid4().hex[:10]}"
        trx = Transaction(
            user_id=session["user_id"],
            stnk_renewal_application_id=application.id,
            order_id=order_id,
            gross_amount=application.admin_fee,
            transaction_status="created",
        )
        db.session.add(trx)
        db.session.flush()

        if should_use_demo_payment():
            mark_transaction_paid(trx)
            db.session.commit()
            return jsonify({"order_id": trx.order_id, "demo_paid": True})

        payload = {
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": application.admin_fee,
            },
            "customer_details": {
                "first_name": session["user"]["name"],
                "email": session["user"]["email"],
            },
            "item_details": [
                {
                    "id": f"STNK-{application.id}",
                    "price": application.admin_fee,
                    "quantity": 1,
                    "name": f"Perpanjang STNK {application.vehicle.plate_number}",
                }
            ],
            "credit_card": {"secure": True},
        }

        midtrans_response = get_snap_client().create_transaction(payload)
        trx.snap_token = midtrans_response["token"]
        trx.snap_redirect_url = midtrans_response["redirect_url"]
        trx.raw_response = midtrans_response
        db.session.commit()

        return jsonify(
            {
                "order_id": trx.order_id,
                "snap_token": trx.snap_token,
                "redirect_url": trx.snap_redirect_url,
            }
        )

    @app.route("/payments/fine/<int:fine_id>/create", methods=["POST"])
    @login_required
    def create_fine_payment(fine_id):
        fine = (
            Fine.query.join(Vehicle)
            .filter(Fine.id == fine_id, Vehicle.user_id == session["user_id"])
            .first_or_404()
        )

        if fine.status == "paid":
            return jsonify({"message": "Denda sudah dibayar."}), 400

        order_id = f"SAMSATGO-FINE-{fine.id}-{uuid4().hex[:10]}"
        trx = Transaction(
            user_id=session["user_id"],
            fine_id=fine.id,
            order_id=order_id,
            gross_amount=fine.amount,
            transaction_status="created",
        )
        db.session.add(trx)
        db.session.flush()

        if should_use_demo_payment():
            mark_transaction_paid(trx)
            db.session.commit()
            return jsonify({"order_id": trx.order_id, "demo_paid": True})

        payload = {
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": fine.amount,
            },
            "customer_details": {
                "first_name": session["user"]["name"],
                "email": session["user"]["email"],
            },
            "item_details": [
                {
                    "id": f"FINE-{fine.id}",
                    "price": fine.amount,
                    "quantity": 1,
                    "name": f"Denda ETLE {fine.vehicle.plate_number}",
                }
            ],
            "credit_card": {"secure": True},
        }

        midtrans_response = get_snap_client().create_transaction(payload)
        trx.snap_token = midtrans_response["token"]
        trx.snap_redirect_url = midtrans_response["redirect_url"]
        trx.raw_response = midtrans_response
        db.session.commit()

        return jsonify(
            {
                "order_id": trx.order_id,
                "snap_token": trx.snap_token,
                "redirect_url": trx.snap_redirect_url,
            }
        )

    @app.route("/payments/midtrans/notification", methods=["POST"])
    @csrf.exempt
    def midtrans_notification():
        notification = request.get_json()
        status = get_core_client().transactions.notification(notification)

        trx = Transaction.query.filter_by(order_id=status["order_id"]).first_or_404()
        trx.transaction_status = status["transaction_status"]
        trx.fraud_status = status.get("fraud_status")
        trx.payment_type = status.get("payment_type")
        trx.midtrans_transaction_id = status.get("transaction_id")
        trx.raw_response = status

        if trx.transaction_status in ["capture", "settlement"]:
            if trx.fraud_status in [None, "accept"]:
                trx.paid_at = datetime.utcnow()
                if trx.tax_record:
                    trx.tax_record.status = "paid"
                    trx.tax_record.paid_at = trx.paid_at
                if trx.fine:
                    trx.fine.status = "paid"
                if trx.stnk_renewal_application:
                    trx.stnk_renewal_application.status = "paid"
        elif trx.transaction_status in ["cancel", "deny", "expire"]:
            if trx.tax_record and trx.tax_record.status != "paid":
                trx.tax_record.status = "unpaid"
            if trx.fine and trx.fine.status != "paid":
                trx.fine.status = "unpaid"
            if trx.stnk_renewal_application and trx.stnk_renewal_application.status != "paid":
                trx.stnk_renewal_application.status = "submitted"

        db.session.commit()
        return "OK", 200
