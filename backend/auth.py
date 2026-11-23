"""Modulul M1: Autentificare institutionala USV (@usv.ro) si control acces."""

from functools import wraps
from flask import abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
import config
from backend import db


def is_valid_usv_email(email):
    """Verifica daca adresa de email apartine domeniului institutional USV."""
    cleaned = (email or "").strip().lower()
    return "@" in cleaned and any(
        cleaned.endswith(suffix) for suffix in config.ALLOWED_EMAIL_SUFFIXES
    )


def get_current_user():
    """Returneaza dictionarul utilizatorului autentificat sau None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.query_one(
        "SELECT id, email, name, role FROM users WHERE id = ?;", (user_id,)
    )


def login_required(view_func):
    """Decorator care restrictioneaza accesul doar utilizatorilor autentificati."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Autentifică-te cu contul instituțional USV.", "error")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapped


def role_required(*allowed_roles):
    """Decorator care verifica daca utilizatorul are unul din rolurile permise."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user:
                return redirect(url_for("login"))
            if user["role"] not in allowed_roles:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


def register_routes(app):
    """Inregistreaza rutele de autentificare in aplicatia Flask."""
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user_id"):
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            return _handle_login_post()
        return render_template("login.html")

    @app.route("/demo-login/<role>", methods=["POST"])
    def demo_login(role):
        demo_emails = {
            "student": "ana.maria@student.usv.ro",
            "cadru": "ion.popescu@usv.ro",
            "admin": "admin.rrm@usv.ro",
        }
        email = demo_emails.get(role)
        user = db.query_one("SELECT * FROM users WHERE email = ?;", (email,)) if email else None
        if not user:
            flash("Cont demo indisponibil.", "error")
            return redirect(url_for("login"))
        session["user_id"] = user["id"]
        return redirect(url_for("dashboard"))

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Te-ai deconectat cu succes.", "success")
        return redirect(url_for("login"))


def _handle_login_post():
    """Valideaza emailul USV si parola la trimiterea formularului."""
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not is_valid_usv_email(email):
        flash("Acces permis doar cu email instituțional USV (@usv.ro).", "error")
        return render_template("login.html", email=email)
    user = db.query_one("SELECT * FROM users WHERE email = ?;", (email,))
    if not user or not check_password_hash(user["password_hash"], password):
        flash("Email sau parolă incorectă.", "error")
        return render_template("login.html", email=email)
    session["user_id"] = user["id"]
    return redirect(url_for("dashboard"))