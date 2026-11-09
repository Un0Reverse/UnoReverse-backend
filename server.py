"""Serverul backend al aplicației "Products".

Expune un API REST pentru operațiile CRUD asupra entității Product
(Create, Read, Update, Delete) și persistă datele într-o bază de date
SQLite locală, creată prin modulul standard sqlite3.

Stil de scriere a codului: PEP 8 — the Style Guide for Python Code
https://pep8.org/

Rulare:
    pip install -r requirements.txt
    uvicorn server:app --port 3000 --reload

API disponibil pe: http://localhost:3000
Documentația interactivă: http://localhost:3000/docs
"""

import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).parent / "data" / "products.db"

app = FastAPI(title="Products API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductPayload(BaseModel):
    """Datele primite în cererile de creare și actualizare."""

    name: str = Field(min_length=1)
    price: float = Field(ge=0)
    description: str = ""


class Product(ProductPayload):
    """Un produs returnat către client, cu id-ul din baza de date."""

    id: int


def get_connection():
    """Returnează o conexiune către baza de date SQLite."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Creează tabela produselor, dacă nu există deja."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(get_connection()) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS products ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " name TEXT NOT NULL,"
            " price REAL NOT NULL,"
            " description TEXT NOT NULL DEFAULT '')"
        )
        connection.commit()


def row_to_product(row):
    """Convertește un rând din baza de date într-un produs."""
    return Product(
        id=row["id"],
        name=row["name"],
        price=row["price"],
        description=row["description"],
    )


@app.get("/api/products")
def list_products():
    """READ - returnează toate produsele din baza de date."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            "SELECT * FROM products ORDER BY id").fetchall()
    return [row_to_product(row) for row in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    """READ - returnează un singur produs, identificat după id."""
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Produsul cu id-ul {product_id} nu există.",
        )
    return row_to_product(row)


@app.post("/api/products", status_code=201)
def create_product(payload: ProductPayload):
    """CREATE - creează un produs nou."""
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "INSERT INTO products (name, price, description)"
            " VALUES (?, ?, ?)",
            (payload.name.strip(), payload.price,
             payload.description.strip()),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return row_to_product(row)


@app.put("/api/products/{product_id}")
def update_product(product_id: int, payload: ProductPayload):
    """UPDATE - actualizează un produs existent."""
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Produsul cu id-ul {product_id} nu există.",
            )
        connection.execute(
            "UPDATE products SET name = ?, price = ?, description = ?"
            " WHERE id = ?",
            (payload.name.strip(), payload.price,
             payload.description.strip(), product_id),
        )
        connection.commit()
        updated = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
    return row_to_product(updated)


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    """DELETE - șterge un produs existent."""
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Produsul cu id-ul {product_id} nu există.",
            )
        connection.execute(
            "DELETE FROM products WHERE id = ?",
            (product_id,),
        )
        connection.commit()
    return row_to_product(row)


init_db()
