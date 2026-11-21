"""Modulele M7 si M8: Rapoarte grad de ocupare si administrare resurse/setari."""

from flask import flash, redirect, render_template, request, url_for
from backend import db
from backend.auth import login_required, role_required
from backend.equipment import get_categories, get_filtered_equipment
from backend.rooms import get_all_rooms


def get_rooms_occupancy():
    """Calculeaza gradul de ocupare (%) al celor 17 sali din rezervarile confirmate."""
    rooms = get_all_rooms()
    report = []
    for room in rooms:
        row = db.query_one(
            "SELECT COUNT(*) AS cnt FROM bookings "
            "WHERE resource_type = 'room' AND resource_id = ? AND status = 'confirmed';",
            (room["id"],),
        )
        pct = min(100, (row["cnt"] * 15)) if row else 0
        report.append({"name": room["name"], "percent": pct, "bookings": row["cnt"]})
    return report


def register_routes(app):
    """Inregistreaza rutele de raportare si administrare resurse."""
    @app.route("/admin/reports")
    @login_required
    @role_required("admin")
    def admin_reports():
        occupancy = get_rooms_occupancy()
        return render_template(
            "admin_reports.html",
            active_nav="admin",
            admin_tab="rapoarte",
            occupancy=occupancy,
        )

    @app.route("/admin/resources")
    @login_required
    @role_required("admin")
    def admin_resources():
        rooms = get_all_rooms()
        equipment_list = get_filtered_equipment()
        expiry = db.query_one(
            "SELECT value FROM settings WHERE key = 'pending_expiry_hours';"
        )
        return render_template(
            "admin_resources.html",
            active_nav="admin",
            admin_tab="resurse",
            rooms=rooms,
            equipment_list=equipment_list,
            categories=get_categories(),
            expiry_hours=expiry["value"] if expiry else "48",
        )

    @app.route("/admin/resources/toggle/<res_type>/<int:res_id>", methods=["POST"])
    @login_required
    @role_required("admin")
    def toggle_resource_maintenance(res_type, res_id):
        if res_type == "room":
            _toggle_room_status(res_id)
        elif res_type == "equipment":
            _toggle_equipment_status(res_id)
        return redirect(url_for("admin_resources"))

    @app.route("/admin/settings", methods=["POST"])
    @login_required
    @role_required("admin")
    def update_admin_settings():
        hours = request.form.get("pending_expiry_hours", "48").strip()
        if hours.isdigit() and int(hours) > 0:
            db.execute(
                "UPDATE settings SET value = ? WHERE key = 'pending_expiry_hours';",
                (hours,),
            )
            flash(f"Termenul de expirare a fost actualizat la {hours}h.", "success")
        return redirect(url_for("admin_resources"))


def _toggle_room_status(room_id):
    """Comuta statusul unei sali si al celor 16 statii intre disponibila si mentenanta."""
    room = db.query_one("SELECT status, name FROM rooms WHERE id = ?;", (room_id,))
    if not room:
        return
    new_status = "mentenanta" if room["status"] == "disponibila" else "disponibila"
    db.execute("UPDATE rooms SET status = ? WHERE id = ?;", (new_status, room_id))
    db.execute("UPDATE stations SET status = ? WHERE room_id = ?;", (new_status, room_id))
    flash(f"{room['name']}: status actualizat la '{new_status}'.", "success")


def _toggle_equipment_status(eq_id):
    """Comuta statusul unui echipament intre disponibil si mentenanta."""
    eq = db.query_one("SELECT status, name FROM equipment WHERE id = ?;", (eq_id,))
    if not eq:
        return
    new_status = "mentenanta" if eq["status"] == "disponibil" else "disponibil"
    db.execute("UPDATE equipment SET status = ? WHERE id = ?;", (new_status, eq_id))
    flash(f"{eq['name']}: status actualizat la '{new_status}'.", "success")