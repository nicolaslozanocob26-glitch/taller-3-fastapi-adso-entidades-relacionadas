from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query

from app.database import conectar
from app.schemas import ProductoCrear, ProductoRespuesta

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.get("", response_model=list[ProductoRespuesta])
def listar_productos(
    buscar: str | None = Query(default=None, min_length=1, max_length=100),
    pagina: int = Query(default=1, ge=1),
    limite: int = Query(default=10, ge=1, le=50),
) -> list[dict]:
    sql = "SELECT id, nombre, precio, stock FROM productos"
    parametros: list[object] = []
    if buscar:
        sql += " WHERE nombre LIKE %s"
        parametros.append(f"%{buscar}%")
    sql += " ORDER BY id LIMIT %s OFFSET %s"
    parametros.extend([limite, (pagina - 1) * limite])
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(sql, tuple(parametros))
            return cur.fetchall()


@router.get("/{producto_id}", response_model=ProductoRespuesta)
def obtener_producto(producto_id: int) -> dict:
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT id, nombre, precio, stock FROM productos WHERE id=%s",
                (producto_id,),
            )
            producto = cur.fetchone()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.post("", response_model=ProductoRespuesta, status_code=201)
def crear_producto(datos: ProductoCrear) -> dict:
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s)",
                (datos.nombre, datos.precio, datos.stock),
            )
            nuevo_id = cur.lastrowid
            cur.execute(
                "SELECT id, nombre, precio, stock FROM productos WHERE id=%s", (nuevo_id,)
            )
            return cur.fetchone()


@router.patch("/{producto_id}/stock", response_model=ProductoRespuesta)
def cambiar_stock(
    producto_id: int, stock: int = Query(ge=0)
) -> dict:
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT id FROM productos WHERE id=%s FOR UPDATE", (producto_id,)
            )
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Producto no encontrado")
            cur.execute(
                "UPDATE productos SET stock=%s WHERE id=%s", (stock, producto_id)
            )
            cur.execute(
                "SELECT id, nombre, precio, stock FROM productos WHERE id=%s",
                (producto_id,),
            )
            return cur.fetchone()
