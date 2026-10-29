from fastapi import APIRouter, HTTPException
from pymysql.err import IntegrityError

from app.database import conectar
from app.schemas import ClienteCrear, ClienteRespuesta

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("", response_model=list[ClienteRespuesta])
def listar_clientes() -> list[dict]:
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute("SELECT id, nombre, correo FROM clientes ORDER BY id")
            return cur.fetchall()


@router.get("/{cliente_id}/pedidos")
def pedidos_del_cliente(cliente_id: int) -> list[dict]:
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute("SELECT id FROM clientes WHERE id=%s", (cliente_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            cur.execute(
                "SELECT p.id, p.fecha, p.estado, p.total, c.nombre AS cliente "
                "FROM pedidos p JOIN clientes c ON c.id=p.cliente_id "
                "WHERE p.cliente_id=%s ORDER BY p.fecha DESC, p.id DESC",
                (cliente_id,),
            )
            return cur.fetchall()


@router.get("/{cliente_id}", response_model=ClienteRespuesta)
def obtener_cliente(cliente_id: int) -> dict:
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT id, nombre, correo FROM clientes WHERE id=%s", (cliente_id,)
            )
            cliente = cur.fetchone()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.post("", response_model=ClienteRespuesta, status_code=201)
def crear_cliente(datos: ClienteCrear) -> dict:
    try:
        with conectar() as db:
            with db.cursor() as cur:
                cur.execute(
                    "INSERT INTO clientes (nombre, correo) VALUES (%s, %s)",
                    (datos.nombre, str(datos.correo)),
                )
                nuevo_id = cur.lastrowid
                cur.execute(
                    "SELECT id, nombre, correo FROM clientes WHERE id=%s", (nuevo_id,)
                )
                return cur.fetchone()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="El correo ya está registrado") from exc


@router.put("/{cliente_id}", response_model=ClienteRespuesta)
def actualizar_cliente(cliente_id: int, datos: ClienteCrear) -> dict:
    try:
        with conectar() as db:
            with db.cursor() as cur:
                cur.execute(
                    "SELECT id FROM clientes WHERE id=%s FOR UPDATE", (cliente_id,)
                )
                if cur.fetchone() is None:
                    raise HTTPException(status_code=404, detail="Cliente no encontrado")
                cur.execute(
                    "UPDATE clientes SET nombre=%s, correo=%s WHERE id=%s",
                    (datos.nombre, str(datos.correo), cliente_id),
                )
                cur.execute(
                    "SELECT id, nombre, correo FROM clientes WHERE id=%s", (cliente_id,)
                )
                return cur.fetchone()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="El correo ya está registrado") from exc


@router.delete("/{cliente_id}", status_code=204)
def eliminar_cliente(cliente_id: int) -> None:
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT id FROM clientes WHERE id=%s FOR UPDATE", (cliente_id,)
            )
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            cur.execute(
                "SELECT 1 FROM pedidos WHERE cliente_id=%s LIMIT 1", (cliente_id,)
            )
            if cur.fetchone() is not None:
                raise HTTPException(
                    status_code=409,
                    detail="No se puede eliminar un cliente que tiene pedidos",
                )
            cur.execute("DELETE FROM clientes WHERE id=%s", (cliente_id,))
