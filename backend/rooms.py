"""Modulul M2: Gestionarea celor 17 sali, 272 statii si dashboard-ului."""

from flask import abort, render_template, request
from backend import db
from backend.auth import get_current_user, login_required


def get_all_rooms():
    """Returneaza lista celor 17 sali ordonate dupa cod."""
    return db.query_all(
        "SELECT id, code, name, schedule, stations_count, status "
        "FROM rooms ORDER BY id ASC;"
    )


def get_room_by_id(room_id):
    """Returneaza detaliile unei sali sau None."""
    return db.query_one(
        "SELECT id, code, name, schedule, stations_count, status "
        "FROM rooms WHERE id = ?;",
        (room_id,),
    )


def get_stations_by_room(room_id):
    """Returneaza cele 16 statii ale unei sali."""
    return db.query_all(
        "SELECT id, room_id, number, label, status "
        "FROM stations WHERE room_id = ? ORDER BY number ASC;",
        (room_id,),
    )


def register_routes(app):
    """Inregistreaza rutele pentru dashboard, sali si detalii sala."""
    @app.route("/")
    @app.route("/dashboard")
    @login_required
    def dashboard():
        user = get_current_user()
        selected_room_id = request.args.get("room_id", 1, type=int)
        rooms = get_all_rooms()
        selected_room = get_room_by_id(selected_room_id) or (rooms[0] if rooms else None)
        stats = _get_dashboard_stats()
        active_bookings = _get_user_active_bookings(user["id"])
        calendar_grid = _build_weekly_calendar(selected_room["id"] if selected_room else 1)
        return render_template(
            "dashboard.html",
            active_nav="dashboard",
            rooms=rooms,
            selected_room=selected_room,
            stats=stats,
            active_bookings=active_bookings,
            calendar_grid=calendar_grid,
        )

    @app.route("/rooms")
    @login_required
    def rooms_list():
        rooms = get_all_rooms()
        return render_template("rooms.html", active_nav="cautare", rooms=rooms)

    @app.route("/rooms/<int:room_id>")
    @login_required
    def room_detail(room_id):
        room = get_room_by_id(room_id)
        if not room:
            abort(404)
        stations = get_stations_by_room(room_id)
        room_equipment = db.query_all(
            "SELECT e.id, e.code, e.name, e.status, c.name AS category_name "
            "FROM equipment e JOIN categories c ON c.id = e.category_id "
            "WHERE e.room_id = ? ORDER BY e.id ASC;",
            (room_id,),
        )
        return render_template(
            "room_detail.html",
            active_nav="cautare",
            room=room,
            stations=stations,
            room_equipment=room_equipment,
        )


def _get_dashboard_stats():
    """Calculeaza indicatorii rapizi afisati pe dashboard."""
    rooms_cnt = db.query_one("SELECT COUNT(*) AS c FROM rooms;")["c"]
    stations_cnt = db.query_one("SELECT COUNT(*) AS c FROM stations;")["c"]
    eq_cnt = db.query_one("SELECT COUNT(*) AS c FROM equipment;")["c"]
    pending_cnt = db.query_one(
        "SELECT COUNT(*) AS c FROM bookings WHERE status = 'pending';"
    )["c"]
    return {
        "rooms": rooms_cnt,
        "stations": stations_cnt,
        "equipment": eq_cnt,
        "pending": pending_cnt,
    }


def _get_user_active_bookings(user_id):
    """Returneaza rezervarile active sau in asteptare ale utilizatorului."""
    return db.query_all(
        "SELECT id, code, resource_type, resource_id, booking_type, "
        "start_time, end_time, status FROM bookings "
        "WHERE user_id = ? AND status IN ('pending', 'confirmed') "
        "ORDER BY start_time ASC LIMIT 5;",
        (user_id,),
    )


def _build_weekly_calendar(room_id):
    """Construieste grila orara Lun-Vin pentru sala selectata."""
    bookings = db.query_all(
        "SELECT start_time, end_time FROM bookings "
        "WHERE resource_type = 'room' AND resource_id = ? AND status = 'confirmed';",
        (room_id,),
    )
    hours = ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00"]
    days = ["Lun", "Mar", "Mier", "Joi", "Vin"]
    grid = []
    for hour in hours:
        row_slots = []
        for idx, _ in enumerate(days):
            busy = any(hour in b["start_time"] for b in bookings) and idx == 1
            row_slots.append(busy)
        grid.append({"hour": hour, "slots": row_slots})
    return {"days": days, "rows": grid}