"""Configurarea centrala a aplicatiei Research Resource Manager USV."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "rrm.sqlite3")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")

SECRET_KEY = os.environ.get("RRM_SECRET_KEY", "rrm-dev-key-change-in-production")

APP_NAME = "USV | Research Resource Manager"

DEFAULT_ROOM_SCHEDULE = "08:00-20:00"
DEFAULT_STATIONS_COUNT = 16

STATUS_AVAILABLE = "disponibila"
STATUS_MAINTENANCE = "mentenanta"
ROOM_STATUSES = (STATUS_AVAILABLE, STATUS_MAINTENANCE)
