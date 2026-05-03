import os

from dotenv import load_dotenv
from flask import Flask

from config import DevelopmentConfig, ProductionConfig
from samsatgo.extensions import csrf, db, migrate
from samsatgo.formatters import rupiah


def create_app():
    load_dotenv()

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )

    config_class = ProductionConfig if os.getenv("FLASK_ENV") == "production" else DevelopmentConfig
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    app.jinja_env.filters["rupiah"] = rupiah

    from samsatgo.routes.auth import register_auth_routes
    from samsatgo.routes.main import register_main_routes
    from samsatgo.routes.payment import register_payment_routes

    register_auth_routes(app)
    register_main_routes(app)
    register_payment_routes(app)
    register_cli(app)

    return app


def register_cli(app):
    @app.cli.command("seed")
    def seed():
        from datetime import date

        from samsatgo.models import Fine, TaxRecord, User, Vehicle

        db.create_all()

        user = User.query.filter_by(email="user@example.com").first()
        if not user:
            user = User(
                name="Budi Santoso",
                email="user@example.com",
                nik="3276010101010001",
                phone="081234567890",
            )
            user.set_password("password123")
            db.session.add(user)
            db.session.flush()

        vehicle = Vehicle.query.filter_by(plate_number="AG 1234 RFS").first()
        if not vehicle:
            vehicle = Vehicle(
                user_id=user.id,
                plate_number="AG 1234 RFS",
                owner_name=user.name,
                brand="Toyota",
                model="Avanza 1.3 G",
                year=2021,
                color="Hitam",
                frame_number="MHKA1234598765",
                engine_number="98765",
                stnk_number="STNK-2026-0001",
            )
            db.session.add(vehicle)
            db.session.flush()

        tax_record = TaxRecord.query.filter_by(vehicle_id=vehicle.id, tax_year=2026).first()
        if not tax_record:
            db.session.add(
                TaxRecord(
                    vehicle_id=vehicle.id,
                    tax_year=2026,
                    base_tax=2150000,
                    swdkllj=35000,
                    admin_fee=5000,
                    fine_amount=0,
                    total_amount=2190000,
                    due_date=date(2026, 5, 15),
                    status="unpaid",
                )
            )
        else:
            tax_record.base_tax = 2150000
            tax_record.swdkllj = 35000
            tax_record.admin_fee = 5000
            tax_record.fine_amount = 0
            tax_record.total_amount = 2190000
            tax_record.due_date = date(2026, 5, 15)
            tax_record.status = "unpaid"
            tax_record.paid_at = None

        fine = Fine.query.filter_by(vehicle_id=vehicle.id, violation_code="ETLE-001").first()
        if not fine:
            db.session.add(
                Fine(
                    vehicle_id=vehicle.id,
                    violation_code="ETLE-001",
                    description="Melanggar Lampu Merah",
                    location="Surabaya",
                    amount=500000,
                    violation_date=date(2026, 4, 20),
                    status="unpaid",
                )
            )
        else:
            fine.description = "Melanggar Lampu Merah"
            fine.location = "Surabaya"
            fine.amount = 500000
            fine.violation_date = date(2026, 4, 20)
            fine.status = "unpaid"

        db.session.commit()
        print("Seed data SamsatGo berhasil dibuat.")
