"""Conexiune si helper-e SQL parametrizate pentru intreaga aplicatie."""

import os
import sqlite3
from werkzeug.security import generate_password_hash
import config


def get_connection():
    """Deschide o conexiune SQLite cu suport Row si foreign keys."""
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def query_all(sql, params=()):
    """Ruleaza un SELECT si returneaza lista de dictionare."""
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def query_one(sql, params=()):
    """Ruleaza un SELECT si returneaza primul rezultat ca dictionar sau None."""
    conn = get_connection()
    try:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row is not None else None
    finally:
        conn.close()


def execute(sql, params=()):
    """Ruleaza o comanda de scriere, salveaza si returneaza rowcount."""
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def execute_returning_id(sql, params=()):
    """Ruleaza un INSERT, salveaza si returneaza id-ul randului nou."""
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _seed_demo_users(conn):
    """Populeaza conturile demo USV daca nu exista deja."""
    demo_users = [
        ("ana.maria@student.usv.ro", "Ana Maria", "student123", "student"),
        ("ion.popescu@usv.ro", "Ion Popescu", "cadru123", "cadru"),
        ("admin.rrm@usv.ro", "Admin RRM", "admin123", "admin"),
    ]
    for email, name, raw_pass, role in demo_users:
        conn.execute(
            "INSERT OR IGNORE INTO users (email, name, password_hash, role) "
            "VALUES (?, ?, ?, ?);",
            (email, name, generate_password_hash(raw_pass), role),
        )


def init_db():
    """Aplica schema.sql si seed.sql la pornirea aplicatiei (idempotent)."""
    conn = get_connection()
    try:
        with open(config.SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        if os.path.exists(config.SEED_PATH):
            with open(config.SEED_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
        _seed_demo_users(conn)
        conn.commit()
    finally:
        conn.close()