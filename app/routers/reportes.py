from fastapi import APIRouter

from app.database import conectar

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/ventas-por-cliente")
def ventas_por_cliente() -> list[dict]:
    """Resume pedidos confirmados y ventas por cliente, incluidos los que no tienen pedidos."""
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT c.id AS cliente_id, c.nombre AS cliente, "
                "COUNT(DISTINCT CASE WHEN p.estado='confirmado' THEN p.id END) "
                "AS pedidos_confirmados, "
                "COALESCE(SUM(CASE WHEN p.estado='confirmado' THEN p.total ELSE 0 END), 0) "
                "AS ventas_confirmadas "
                "FROM clientes c LEFT JOIN pedidos p ON p.cliente_id=c.id "
                "GROUP BY c.id, c.nombre ORDER BY c.id"
            )
            return cur.fetchall()
