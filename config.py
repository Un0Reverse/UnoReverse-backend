"""Configurarea centrala a aplicatiei Research Resource Manager USV."""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "rrm.sqlite3")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
SEED_PATH = os.path.join(BASE_DIR, "database", "seed.sql")

_SIBLING_FRONTEND = os.path.abspath(
    os.path.join(BASE_DIR, "..", "UnoReverse-frontend", "frontend")
)
_LOCAL_FRONTEND = os.path.join(BASE_DIR, "frontend")
FRONTEND_DIR = (
    _SIBLING_FRONTEND if os.path.isdir(_SIBLING_FRONTEND) else _LOCAL_FRONTEND
)
TEMPLATE_FOLDER = os.path.join(FRONTEND_DIR, "templates")
STATIC_FOLDER = os.path.join(FRONTEND_DIR, "static")

SECRET_KEY = os.environ.get("RRM_SECRET_KEY", "rrm-usv-secret-key-2026")
APP_NAME = "Research Resource Manager"
ALLOWED_EMAIL_SUFFIXES = ("@usv.ro", "@student.usv.ro")

DEFAULT_ROOM_SCHEDULE = "08:00-20:00"
DEFAULT_STATIONS_COUNT = 16
STATUS_AVAILABLE = "disponibila"
STATUS_MAINTENANCE = "mentenanta"

SMTP_HOST = os.environ.get("RRM_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("RRM_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("RRM_SMTP_USER", "")
SMTP_PASS = os.environ.get("RRM_SMTP_PASS", "")