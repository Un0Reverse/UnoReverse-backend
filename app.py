"""Nucleul comun M0: pornirea aplicatiei si inregistrarea modulelor."""

from flask import Flask, render_template, session
import config
from backend import db


def create_app():
    """Creeaza aplicatia Flask, initializeaza baza de date si rutele."""
    app = Flask(
        __name__,
        template_folder=config.TEMPLATE_FOLDER,
        static_folder=config.STATIC_FOLDER,
    )
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["APP_NAME"] = config.APP_NAME

    db.init_db()
    _register_context_processors(app)
    _register_error_handlers(app)
    _register_modules(app)
    return app


def _register_context_processors(app):
    """Injecteaza datele utilizatorului curent si notificari in toate sabloanele."""
    @app.context_processor
    def inject_globals():
        user_id = session.get("user_id")
        current_user = None
        unread_count = 0
        if user_id:
            current_user = db.query_one(
                "SELECT id, email, name, role FROM users WHERE id = ?;",
                (user_id,),
            )
            row = db.query_one(
                "SELECT COUNT(*) AS cnt FROM notifications "
                "WHERE user_id = ? AND is_read = 0;",
                (user_id,),
            )
            unread_count = row["cnt"] if row else 0
        return {
            "current_user": current_user,
            "unread_count": unread_count,
            "app_name": config.APP_NAME,
        }


def _register_error_handlers(app):
    """Inregistreaza paginile de eroare 403, 404 si 500."""
    @app.errorhandler(403)
    def forbidden(error):
        return render_template(
            "error.html", code=403,
            message="Nu ai permisiuni pentru această secțiune."
        ), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template(
            "error.html", code=404,
            message="Pagina solicitată nu a fost găsită."
        ), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template(
            "error.html", code=500,
            message="Eroare internă de server."
        ), 500


def _register_modules(app):
    """Inregistreaza rutele fiecarui modul (M1 -> M8)."""
    from backend import auth, rooms, equipment, booking, approval, notifications, reports
    auth.register_routes(app)
    rooms.register_routes(app)
    equipment.register_routes(app)
    booking.register_routes(app)
    approval.register_routes(app)
    notifications.register_routes(app)
    reports.register_routes(app)


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)