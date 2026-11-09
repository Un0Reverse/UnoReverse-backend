"""Conexiune si helper-e SQL parametrizate pentru intreaga aplicatie."""
import sqlite3

import config


def get_connection():
    """Deschide o conexiune SQLite cu suport Row si foreign keys."""
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


def init_db():
    """Aplica schema.sql la pornirea aplicatiei (idempotent)."""
    conn = get_connection()
    try:
        with open(config.SCHEMA_PATH, "r", encoding="utf-8") as file:
            conn.executescript(file.read())
        conn.commit()
    finally:
        conn.close()
