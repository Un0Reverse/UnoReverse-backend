"""Modulul M6: Notificari in-app, alerte email USV (smtplib) si reminder 24h."""

from email.message import EmailMessage
import smtplib
from flask import flash, redirect, render_template, url_for
import config
from backend import db
from backend.auth import get_current_user, login_required


def add_notification(user_id, tip, title, message, booking_id=None):
    """Contract public M6: creeaza o notificare in-app si trimite email daca e configurat."""
    db.execute(
        "INSERT INTO notifications (user_id, booking_id, type, title, message) "
        "VALUES (?, ?, ?, ?, ?);",
        (user_id, booking_id, tip, title, message),
    )
    user = db.query_one("SELECT email FROM users WHERE id = ?;", (user_id,))
    if user and config.SMTP_HOST:
        _send_email_alert(user["email"], f"[RRM USV] {title}", message)


def notify_admins(tip, title, message, booking_id=None):
    """Trimite o notificare catre toti administratorii sistemului."""
    admins = db.query_all("SELECT id FROM users WHERE role = 'admin';")
    for admin in admins:
        add_notification(admin["id"], tip, title, message, booking_id)


def send_24h_reminders():
    """Genereaza notificari reminder pentru rezervarile confirmate din urmatoarele 24h."""
    upcoming = db.query_all(
        "SELECT b.id, b.code, b.user_id, b.start_time FROM bookings b "
        "WHERE b.status = 'confirmed' "
        "AND datetime(b.start_time) BETWEEN datetime('now') AND datetime('now', '+24 hours') "
        "AND NOT EXISTS ("
        "  SELECT 1 FROM notifications n WHERE n.booking_id = b.id AND n.type = 'reminder_24h'"
        ");"
    )
    for b in upcoming:
        add_notification(
            b["user_id"], "reminder_24h", "Reminder 24h",
            f"Rezervarea {b['code']} începe la {b['start_time']}. Eliberează resursa la final.",
            b["id"],
        )
    return len(upcoming)


def register_routes(app):
    """Inregistreaza rutele pentru vizualizarea si marcarea notificarilor."""
    @app.route("/notifications")
    @login_required
    def notifications_list():
        user = get_current_user()
        items = db.query_all(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC;",
            (user["id"],),
        )
        return render_template(
            "notifications.html", active_nav="notificari", notifications=items
        )

    @app.route("/notifications/read-all", methods=["POST"])
    @login_required
    def mark_notifications_read():
        user = get_current_user()
        db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?;", (user["id"],))
        flash("Toate notificările au fost marcate ca citite.", "success")
        return redirect(url_for("notifications_list"))


def _send_email_alert(to_email, subject, body):
    """Trimite alerta email prin serverul SMTP USV folosind biblioteca standard."""
    msg = EmailMessage()
    msg["From"] = config.SMTP_USER or "rrm@usv.ro"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=5) as server:
            server.starttls()
            if config.SMTP_USER and config.SMTP_PASS:
                server.login(config.SMTP_USER, config.SMTP_PASS)
            server.send_message(msg)
    except OSError:
        pass