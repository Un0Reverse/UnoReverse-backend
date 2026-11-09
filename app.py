"""Nucleul comun M0: pornirea aplicatiei si inregistrarea rutei home."""
import os

from flask import Flask, render_template

import config
from backend import db


def create_app():
    """Creeaza aplicatia Flask, initializeaza baza de date si rutele."""
    app = Flask(
        __name__,
        template_folder=os.path.join("frontend", "templates"),
        static_folder=os.path.join("frontend", "static"),
    )
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["APP_NAME"] = config.APP_NAME
    db.init_db()
    _register_error_handlers(app)
    _register_routes(app)
    return app


def _register_error_handlers(app):
    """Inregistreaza paginile de eroare 404 si 500."""

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404,
                               message="Pagina nu a fost gasita."), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("error.html", code=500,
                               message="Eroare interna de server."), 500


def _register_routes(app):
    """Inregistreaza rutele nucleului; alte module isi adauga aici rutele."""

    @app.route("/")
    def home():
        rooms = db.query_all(
            "SELECT id, name, schedule, stations_count, status "
            "FROM rooms ORDER BY id ASC;"
        )
        return render_template("home.html", rooms=rooms)


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
