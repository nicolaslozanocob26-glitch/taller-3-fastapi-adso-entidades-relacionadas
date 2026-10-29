from decimal import Decimal

from fastapi import APIRouter, HTTPException

from app.database import conectar
from app.schemas import PedidoCrear

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("", status_code=201)
def crear_pedido(datos: PedidoCrear) -> dict:
    ids = [item.producto_id for item in datos.items]
    if len(set(ids)) != len(ids):
        raise HTTPException(
            status_code=422, detail="No repita el mismo producto en un pedido"
        )

    with conectar() as db:
        with db.cursor() as cur:
            cur.execute("SELECT id FROM clientes WHERE id=%s", (datos.cliente_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")

            # Bloquear en orden estable reduce conflictos entre pedidos simultáneos.
            detalles: list[tuple[int, int, Decimal, Decimal]] = []
            total = Decimal("0.00")
            for item in sorted(datos.items, key=lambda registro: registro.producto_id):
                cur.execute(
                    "SELECT id, precio, stock FROM productos WHERE id=%s FOR UPDATE",
                    (item.producto_id,),
                )
                producto = cur.fetchone()
                if producto is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Producto {item.producto_id} no encontrado",
                    )
                if producto["stock"] < item.cantidad:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Stock insuficiente del producto {item.producto_id}",
                    )
                subtotal = producto["precio"] * item.cantidad
                total += subtotal
                detalles.append(
                    (item.producto_id, item.cantidad, producto["precio"], subtotal)
                )

            cur.execute(
                "INSERT INTO pedidos (cliente_id, estado, total) "
                "VALUES (%s, 'confirmado', %s)",
                (datos.cliente_id, total),
            )
            pedido_id = cur.lastrowid
            for producto_id, cantidad, precio, subtotal in detalles:
                cur.execute(
                    "INSERT INTO detalle_pedidos "
                    "(pedido_id, producto_id, cantidad, precio_unitario, subtotal) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (pedido_id, producto_id, cantidad, precio, subtotal),
                )
                cur.execute(
                    "UPDATE productos SET stock=stock-%s WHERE id=%s",
                    (cantidad, producto_id),
                )

            return {
                "id": pedido_id,
                "cliente_id": datos.cliente_id,
                "estado": "confirmado",
                "total": total,
                "items": len(detalles),
            }


@router.get("")
def listar_pedidos() -> list[dict]:
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT p.id, p.fecha, p.estado, p.total, c.nombre AS cliente "
                "FROM pedidos p JOIN clientes c ON c.id=p.cliente_id "
                "ORDER BY p.id DESC"
            )
            return cur.fetchall()


@router.get("/{pedido_id}")
def obtener_pedido(pedido_id: int) -> dict:
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT p.id, p.fecha, p.estado, p.total, c.nombre AS cliente "
                "FROM pedidos p JOIN clientes c ON c.id=p.cliente_id "
                "WHERE p.id=%s",
                (pedido_id,),
            )
            pedido = cur.fetchone()
            if pedido is None:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")
            cur.execute(
                "SELECT d.producto_id, pr.nombre AS producto, d.cantidad, "
                "d.precio_unitario, d.subtotal "
                "FROM detalle_pedidos d "
                "JOIN productos pr ON pr.id=d.producto_id "
                "WHERE d.pedido_id=%s ORDER BY d.id",
                (pedido_id,),
            )
            pedido["items"] = cur.fetchall()
            return pedido


@router.post("/{pedido_id}/cancelar")
def cancelar_pedido(pedido_id: int) -> dict:
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT id, estado FROM pedidos WHERE id=%s FOR UPDATE", (pedido_id,)
            )
            pedido = cur.fetchone()
            if pedido is None:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")
            if pedido["estado"] != "confirmado":
                raise HTTPException(
                    status_code=409,
                    detail="Solo se puede cancelar un pedido confirmado",
                )

            cur.execute(
                "SELECT producto_id, cantidad FROM detalle_pedidos "
                "WHERE pedido_id=%s ORDER BY producto_id",
                (pedido_id,),
            )
            detalles = cur.fetchall()
            for detalle in detalles:
                cur.execute(
                    "SELECT id FROM productos WHERE id=%s FOR UPDATE",
                    (detalle["producto_id"],),
                )
                if cur.fetchone() is None:
                    raise HTTPException(
                        status_code=409,
                        detail="No se puede devolver el stock de un producto inexistente",
                    )
                cur.execute(
                    "UPDATE productos SET stock=stock+%s WHERE id=%s",
                    (detalle["cantidad"], detalle["producto_id"]),
                )

            cur.execute(
                "UPDATE pedidos SET estado='cancelado' WHERE id=%s", (pedido_id,)
            )
            return {
                "id": pedido_id,
                "estado": "cancelado",
                "unidades_devueltas": sum(detalle["cantidad"] for detalle in detalles),
            }
