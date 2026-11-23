"""Modulul M4: Motorul de rezervari, prevenirea suprapunerilor si istoric."""

from datetime import datetime
from flask import flash, redirect, render_template, request, url_for
from backend import db
from backend.auth import get_current_user, login_required
from backend.equipment import get_equipment_by_id
from backend.notifications import notify_admins
from backend.rooms import get_room_by_id


def check_availability(resource_type, resource_id, start_time, end_time):
    """Verifica daca resursa este disponibila in intervalul [start_time, end_time)."""
    if start_time >= end_time:
        return False, "Ora de sfârșit trebuie să fie după ora de început."
    status_ok, status_msg = _check_resource_operational(resource_type, resource_id)
    if not status_ok:
        return False, status_msg
    direct = db.query_one(
        "SELECT id FROM bookings WHERE resource_type = ? AND resource_id = ? "
        "AND status IN ('pending', 'confirmed') "
        "AND start_time < ? AND end_time > ?;",
        (resource_type, resource_id, end_time, start_time),
    )
    if direct:
        return False, "Intervalul se suprapune cu o rezervare existentă."
    return _check_room_station_conflict(resource_type, resource_id, start_time, end_time)


def get_resource_display_name(resource_type, resource_id):
    """Returneaza denumirea lizibila a resursei rezervate."""
    if resource_type == "room":
        room = get_room_by_id(resource_id)
        return f"{room['name']} (întreagă)" if room else f"Sală #{resource_id}"
    if resource_type == "station":
        row = db.query_one(
            "SELECT s.label, r.name AS room_name FROM stations s "
            "JOIN rooms r ON r.id = s.room_id WHERE s.id = ?;",
            (resource_id,),
        )
        return f"{row['room_name']} · {row['label']}" if row else f"Stație #{resource_id}"
    eq = get_equipment_by_id(resource_id)
    return eq["name"] if eq else f"Echipament #{resource_id}"


def register_routes(app):
    """Inregistreaza rutele pentru creare, vizualizare si anulare rezervari."""
    @app.route("/booking/new", methods=["GET", "POST"])
    @login_required
    def new_booking():
        if request.method == "POST":
            return _handle_create_booking()
        res_type = request.args.get("resource_type", "room")
        res_id = request.args.get("resource_id", 1, type=int)
        res_name = get_resource_display_name(res_type, res_id)
        return render_template(
            "booking_form.html",
            active_nav="cautare",
            resource_type=res_type,
            resource_id=res_id,
            resource_name=res_name,
        )

    @app.route("/my-bookings")
    @login_required
    def my_bookings():
        user = get_current_user()
        rows = db.query_all(
            "SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC;",
            (user["id"],),
        )
        for row in rows:
            row["resource_name"] = get_resource_display_name(
                row["resource_type"], row["resource_id"]
            )
        return render_template("my_bookings.html", active_nav="rezervari", bookings=rows)

    @app.route("/booking/<int:booking_id>/cancel", methods=["POST"])
    @login_required
    def cancel_booking(booking_id):
        user = get_current_user()
        booking = db.query_one(
            "SELECT * FROM bookings WHERE id = ? AND user_id = ?;",
            (booking_id, user["id"]),
        )
        if not booking or booking["status"] not in ("pending", "confirmed"):
            flash("Rezervarea nu poate fi anulată.", "error")
            return redirect(url_for("my_bookings"))
        db.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?;", (booking_id,))
        res_name = get_resource_display_name(booking["resource_type"], booking["resource_id"])
        notify_admins(
            "anulare",
            "Rezervare anulată",
            f"{booking['code']} · {res_name} — intervalul a fost deblocat automat.",
            booking_id,
        )
        flash(f"Rezervarea {booking['code']} a fost anulată.", "success")
        return redirect(url_for("my_bookings"))


def _check_resource_operational(resource_type, resource_id):
    """Verifica daca resursa nu este in mentenanta sau ocupata permanent."""
    if resource_type == "room":
        room = get_room_by_id(resource_id)
        if not room or room["status"] != "disponibila":
            return False, "Sala selectată este în mentenanță."
    elif resource_type == "station":
        row = db.query_one(
            "SELECT s.status AS st_status, r.status AS rm_status "
            "FROM stations s JOIN rooms r ON r.id = s.room_id WHERE s.id = ?;",
            (resource_id,),
        )
        if not row or row["st_status"] != "disponibila" or row["rm_status"] != "disponibila":
            return False, "Stația sau sala este în mentenanță."
    elif resource_type == "equipment":
        eq = get_equipment_by_id(resource_id)
        if not eq or eq["status"] != "disponibil":
            return False, "Echipamentul nu este disponibil."
    return True, "OK"


def _check_room_station_conflict(resource_type, resource_id, start_time, end_time):
    """Previne suprapunerea intre rezervarea unei sali intregi si statiile ei."""
    if resource_type == "room":
        conflict = db.query_one(
            "SELECT b.id FROM bookings b JOIN stations s ON b.resource_id = s.id "
            "WHERE b.resource_type = 'station' AND s.room_id = ? "
            "AND b.status IN ('pending', 'confirmed') "
            "AND b.start_time < ? AND b.end_time > ?;",
            (resource_id, end_time, start_time),
        )
        if conflict:
            return False, "Există deja stații rezervate în această sală pe intervalul ales."
    elif resource_type == "station":
        st = db.query_one("SELECT room_id FROM stations WHERE id = ?;", (resource_id,))
        if st:
            conflict = db.query_one(
                "SELECT id FROM bookings WHERE resource_type = 'room' AND resource_id = ? "
                "AND status IN ('pending', 'confirmed') "
                "AND start_time < ? AND end_time > ?;",
                (st["room_id"], end_time, start_time),
            )
            if conflict:
                return False, "Întreaga sală este deja rezervată în acest interval."
    return True, "Disponibil"


def _handle_create_booking():
    """Valideaza formularul de rezervare, verifica disponibilitatea si salveaza."""
    user = get_current_user()
    res_type = request.form.get("resource_type", "room")
    res_id = request.form.get("resource_id", type=int)
    b_type = request.form.get("booking_type", "orara")
    date_str = request.form.get("date", "")
    start_h = "08:00" if b_type == "zi" else request.form.get("start_hour", "10:00")
    end_h = "20:00" if b_type == "zi" else request.form.get("end_hour", "12:00")
    accepted = 1 if request.form.get("accepted_terms") == "on" else 0
    res_name = get_resource_display_name(res_type, res_id)

    if not accepted:
        flash("Trebuie să accepți Termenii și Condițiile pentru a trimite cererea.", "error")
        return render_template(
            "booking_form.html", active_nav="cautare",
            resource_type=res_type, resource_id=res_id, resource_name=res_name,
        )

    start_time = f"{date_str} {start_h}"
    end_time = f"{date_str} {end_h}"
    ok, reason = check_availability(res_type, res_id, start_time, end_time)
    if not ok:
        flash(reason, "error")
        return render_template(
            "booking_form.html", active_nav="cautare",
            resource_type=res_type, resource_id=res_id, resource_name=res_name,
        )

    code = f"R-{datetime.now().strftime('%H%M%S')}"
    new_id = db.execute_returning_id(
        "INSERT INTO bookings (code, user_id, resource_type, resource_id, "
        "booking_type, start_time, end_time, status, accepted_terms) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 1);",
        (code, user["id"], res_type, res_id, b_type, start_time, end_time),
    )
    notify_admins(
        "cerere_noua",
        "Cerere nouă în așteptare",
        f"{code} · {res_name} ({start_time} – {end_h}) așteaptă aprobare.",
        new_id,
    )
    flash(f"Cerere trimisă: {code} — status: În așteptare.", "success")
    return redirect(url_for("my_bookings"))