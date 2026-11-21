"""Modulul M5: Coada de aprobare, departajare pe roluri si expirare automata."""

from flask import flash, redirect, render_template, url_for
from backend import db
from backend.auth import login_required, role_required
from backend.booking import check_availability, get_resource_display_name
from backend.notifications import add_notification


def expire_stale_bookings():
    """Marcheaza ca expirate cererile pending mai vechi decat termenul din settings."""
    setting = db.query_one(
        "SELECT value FROM settings WHERE key = 'pending_expiry_hours';"
    )
    hours = int(setting["value"]) if setting else 48
    db.execute(
        "UPDATE bookings SET status = 'expired' "
        "WHERE status = 'pending' "
        "AND datetime(created_at, '+' || ? || ' hours') <= datetime('now');",
        (hours,),
    )


def register_routes(app):
    """Inregistreaza rutele de aprobare/respingere pentru administrator."""
    @app.route("/admin/approvals")
    @login_required
    @role_required("admin")
    def admin_approvals():
        expire_stale_bookings()
        pending = db.query_all(
            "SELECT b.*, u.name AS user_name, u.role AS user_role "
            "FROM bookings b JOIN users u ON u.id = b.user_id "
            "WHERE b.status = 'pending' "
            "ORDER BY CASE u.role WHEN 'cadru' THEN 1 WHEN 'student' THEN 2 ELSE 3 END, "
            "b.created_at ASC;"
        )
        for item in pending:
            item["resource_name"] = get_resource_display_name(
                item["resource_type"], item["resource_id"]
            )
        return render_template(
            "admin_approvals.html",
            active_nav="admin",
            admin_tab="aprobari",
            pending=pending,
        )

    @app.route("/admin/approvals/<int:booking_id>/<action>", methods=["POST"])
    @login_required
    @role_required("admin")
    def process_approval(booking_id, action):
        booking = db.query_one("SELECT * FROM bookings WHERE id = ?;", (booking_id,))
        if not booking or booking["status"] != "pending":
            flash("Cererea nu mai este în așteptare.", "error")
            return redirect(url_for("admin_approvals"))
        res_name = get_resource_display_name(booking["resource_type"], booking["resource_id"])
        if action == "approve":
            _approve_booking(booking, res_name)
        else:
            _reject_booking(booking, res_name)
        return redirect(url_for("admin_approvals"))


def _approve_booking(booking, res_name):
    """Aproba o rezervare dupa re-verificarea disponibilitatii."""
    db.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?;", (booking["id"],))
    ok, reason = check_availability(
        booking["resource_type"], booking["resource_id"],
        booking["start_time"], booking["end_time"],
    )
    if not ok:
        db.execute("UPDATE bookings SET status = 'pending' WHERE id = ?;", (booking["id"],))
        flash(f"Nu se poate aproba: {reason}", "error")
        return
    db.execute("UPDATE bookings SET status = 'confirmed' WHERE id = ?;", (booking["id"],))
    add_notification(
        booking["user_id"], "aprobare", "Rezervare confirmată",
        f"{booking['code']} · {res_name} ({booking['start_time']}) a fost aprobată.",
        booking["id"],
    )
    flash(f"Rezervarea {booking['code']} a fost aprobată.", "success")


def _reject_booking(booking, res_name):
    """Respinge o cerere de rezervare si notifica solicitantul."""
    db.execute("UPDATE bookings SET status = 'rejected' WHERE id = ?;", (booking["id"],))
    add_notification(
        booking["user_id"], "respingere", "Cerere respinsă",
        f"{booking['code']} · {res_name} — resursă indisponibilă sau alocată cu prioritate.",
        booking["id"],
    )
    flash(f"Rezervarea {booking['code']} a fost respinsă.", "success")