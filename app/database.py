"""Conexión MySQL y límite transaccional compartido por los routers."""

import os
from contextlib import contextmanager
from typing import Iterator

import pymysql
from dotenv import load_dotenv

load_dotenv()


@contextmanager
def conectar() -> Iterator[pymysql.connections.Connection]:
    usuario = os.getenv("DB_USER")
    clave = os.getenv("DB_PASSWORD")
    if not usuario or clave is None:
        raise RuntimeError(
            "Falta DB_USER o DB_PASSWORD. Copie .env.example a .env y configure la conexión."
        )

    conexion = pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=usuario,
        password=clave,
        database=os.getenv("DB_NAME", "tienda_adso"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=10,
    )
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
