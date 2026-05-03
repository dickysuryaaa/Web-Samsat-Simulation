from functools import wraps
from urllib.parse import urlparse

from flask import flash, redirect, render_template, request, session, url_for

from samsatgo.extensions import db
from samsatgo.models import User


def login_required(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu untuk mengakses halaman ini.", "warning")
            return redirect(url_for("login", next=request.full_path))
        return view(*args, **kwargs)

    return decorated


def is_safe_next_url(next_url):
    if not next_url:
        return False
    parsed = urlparse(next_url)
    return not parsed.netloc and parsed.scheme == ""


def register_auth_routes(app):
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if "user_id" in session:
            return redirect(url_for("index"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()

            if not user or not user.check_password(password):
                flash("Email atau kata sandi salah.", "error")
                return render_template("login.html"), 401

            session.clear()
            session["user_id"] = user.id
            session["user"] = {"email": user.email, "name": user.name}

            flash(f"Selamat datang, {user.name}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page if is_safe_next_url(next_page) else url_for("index"))

        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if "user_id" in session:
            return redirect(url_for("index"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not name or not email or not password:
                flash("Semua field wajib diisi.", "error")
            elif len(password) < 8:
                flash("Kata sandi minimal 8 karakter.", "error")
            elif User.query.filter_by(email=email).first():
                flash("Email sudah terdaftar.", "error")
            else:
                user = User(name=name, email=email)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()

                session.clear()
                session["user_id"] = user.id
                session["user"] = {"email": user.email, "name": user.name}

                flash(f"Akun berhasil dibuat. Selamat datang, {name}!", "success")
                return redirect(url_for("index"))

        return render_template("register.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Anda telah keluar.", "info")
        return redirect(url_for("index"))

