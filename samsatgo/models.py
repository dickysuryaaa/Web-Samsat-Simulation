from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from samsatgo.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    nik = db.Column(db.String(32), unique=True)
    phone = db.Column(db.String(32))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="citizen")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicles = db.relationship("Vehicle", back_populates="user", cascade="all, delete-orphan")
    transactions = db.relationship("Transaction", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plate_number = db.Column(db.String(20), nullable=False, unique=True, index=True)
    owner_name = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(80), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(40))
    frame_number = db.Column(db.String(80), index=True)
    engine_number = db.Column(db.String(80))
    stnk_number = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="vehicles")
    tax_records = db.relationship("TaxRecord", back_populates="vehicle", cascade="all, delete-orphan")
    fines = db.relationship("Fine", back_populates="vehicle", cascade="all, delete-orphan")
    stnk_renewal_applications = db.relationship(
        "StnkRenewalApplication",
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )


class TaxRecord(db.Model):
    __tablename__ = "tax_records"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)
    tax_year = db.Column(db.Integer, nullable=False)
    base_tax = db.Column(db.Integer, nullable=False)
    swdkllj = db.Column(db.Integer, nullable=False, default=0)
    admin_fee = db.Column(db.Integer, nullable=False, default=0)
    fine_amount = db.Column(db.Integer, nullable=False, default=0)
    total_amount = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date)
    paid_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default="unpaid")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", back_populates="tax_records")
    transactions = db.relationship("Transaction", back_populates="tax_record")


class TaxCheckInquiry(db.Model):
    __tablename__ = "tax_check_inquiries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), index=True)
    tax_record_id = db.Column(db.Integer, db.ForeignKey("tax_records.id"), index=True)
    nrkb = db.Column(db.String(20), nullable=False)
    frame_last_five = db.Column(db.String(5), nullable=False)
    nik = db.Column(db.String(32), nullable=False)
    result_status = db.Column(db.String(30), nullable=False, default="not_found")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User")
    vehicle = db.relationship("Vehicle")
    tax_record = db.relationship("TaxRecord")


class Fine(db.Model):
    __tablename__ = "fines"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)
    violation_code = db.Column(db.String(40))
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(120))
    amount = db.Column(db.Integer, nullable=False)
    violation_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default="unpaid")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", back_populates="fines")
    transactions = db.relationship("Transaction", back_populates="fine")


class FineCheckInquiry(db.Model):
    __tablename__ = "fine_check_inquiries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), index=True)
    fine_id = db.Column(db.Integer, db.ForeignKey("fines.id"), index=True)
    police_number = db.Column(db.String(20), nullable=False)
    frame_number_input = db.Column(db.String(80), nullable=False)
    engine_number_input = db.Column(db.String(80))
    incident_location = db.Column(db.String(120))
    result_status = db.Column(db.String(30), nullable=False, default="not_found")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User")
    vehicle = db.relationship("Vehicle")
    fine = db.relationship("Fine")


class VehicleInfoInquiry(db.Model):
    __tablename__ = "vehicle_info_inquiries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), index=True)
    police_number = db.Column(db.String(20), nullable=False)
    nrkb = db.Column(db.String(20), nullable=False)
    frame_last_five = db.Column(db.String(5), nullable=False)
    nik = db.Column(db.String(32), nullable=False)
    result_status = db.Column(db.String(30), nullable=False, default="not_found")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User")
    vehicle = db.relationship("Vehicle")


class StnkRenewalApplication(db.Model):
    __tablename__ = "stnk_renewal_applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)
    nrkb = db.Column(db.String(20), nullable=False)
    frame_last_five = db.Column(db.String(5), nullable=False)
    nik = db.Column(db.String(32), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    ktp_photo_path = db.Column(db.String(255), nullable=False)
    stnk_photo_path = db.Column(db.String(255), nullable=False)
    vehicle_photo_path = db.Column(db.String(255), nullable=False)
    physical_check_photo_path = db.Column(db.String(255))
    admin_fee = db.Column(db.Integer, nullable=False, default=150000)
    status = db.Column(db.String(30), nullable=False, default="submitted")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User")
    vehicle = db.relationship("Vehicle", back_populates="stnk_renewal_applications")
    transactions = db.relationship("Transaction", back_populates="stnk_renewal_application")


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    tax_record_id = db.Column(db.Integer, db.ForeignKey("tax_records.id"))
    fine_id = db.Column(db.Integer, db.ForeignKey("fines.id"))
    stnk_renewal_application_id = db.Column(db.Integer, db.ForeignKey("stnk_renewal_applications.id"))
    order_id = db.Column(db.String(80), nullable=False, unique=True, index=True)
    gross_amount = db.Column(db.Integer, nullable=False)
    snap_token = db.Column(db.String(255))
    snap_redirect_url = db.Column(db.String(500))
    payment_type = db.Column(db.String(60))
    transaction_status = db.Column(db.String(40), nullable=False, default="created")
    fraud_status = db.Column(db.String(40))
    midtrans_transaction_id = db.Column(db.String(120))
    raw_response = db.Column(db.JSON)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="transactions")
    tax_record = db.relationship("TaxRecord", back_populates="transactions")
    fine = db.relationship("Fine", back_populates="transactions")
    stnk_renewal_application = db.relationship(
        "StnkRenewalApplication",
        back_populates="transactions",
    )
