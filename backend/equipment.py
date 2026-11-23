"""Modulul M3: Catalogul de echipamente si cautarea unificata a resurselor."""

from flask import render_template, request
from backend import db
from backend.auth import login_required
from backend.rooms import get_all_rooms


def get_categories():
    """Returneaza toate categoriile de echipamente."""
    return db.query_all("SELECT id, name FROM categories ORDER BY id ASC;")


def get_equipment_by_id(equipment_id):
    """Returneaza detaliile unui echipament dupa ID."""
    return db.query_one(
        "SELECT e.id, e.code, e.name, e.status, e.room_id, "
        "c.name AS category_name, r.name AS room_name "
        "FROM equipment e "
        "JOIN categories c ON c.id = e.category_id "
        "LEFT JOIN rooms r ON r.id = e.room_id "
        "WHERE e.id = ?;",
        (equipment_id,),
    )


def get_filtered_equipment(category_id=None, status=None):
    """Returneaza echipamentele filtrate optional dupa categorie si status."""
    sql = (
        "SELECT e.id, e.code, e.name, e.status, e.room_id, "
        "c.name AS category_name, r.name AS room_name "
        "FROM equipment e "
        "JOIN categories c ON c.id = e.category_id "
        "LEFT JOIN rooms r ON r.id = e.room_id WHERE 1=1 "
    )
    params = []
    if category_id:
        sql += "AND e.category_id = ? "
        params.append(category_id)
    if status and status != "toate":
        sql += "AND e.status = ? "
        params.append(status)
    sql += "ORDER BY e.id ASC;"
    return db.query_all(sql, tuple(params))


def register_routes(app):
    """Inregistreaza rutele de cautare si filtrare a resurselor."""
    @app.route("/resources")
    @app.route("/equipment")
    @login_required
    def resources_catalog():
        res_type = request.args.get("type", "toate")
        cat_id = request.args.get("category", type=int)
        status = request.args.get("status", "toate")
        rooms = _filter_rooms(res_type, status)
        equipment_list = (
            get_filtered_equipment(cat_id, status)
            if res_type in ("toate", "echipamente")
            else []
        )
        return render_template(
            "equipment.html",
            active_nav="cautare",
            rooms=rooms,
            equipment_list=equipment_list,
            categories=get_categories(),
            selected_type=res_type,
            selected_cat=cat_id or 0,
            selected_status=status,
        )


def _filter_rooms(res_type, status):
    """Filtreaza salile conform selectiei din pagina de cautare."""
    if res_type not in ("toate", "sali"):
        return []
    rooms = get_all_rooms()
    if status == "disponibil":
        return [r for r in rooms if r["status"] == "disponibila"]
    if status == "mentenanta":
        return [r for r in rooms if r["status"] == "mentenanta"]
    if status == "ocupat":
        return []
    return rooms