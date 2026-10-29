from fastapi import FastAPI

from app.routers import clientes, pedidos, productos, reportes

app = FastAPI(
    title="Taller 3 ADSO - Tienda",
    version="3.0.0",
    description=(
        "API relacional para gestionar clientes, productos y pedidos "
        "con detalles y control transaccional de inventario."
    ),
)

app.include_router(clientes.router)
app.include_router(productos.router)
app.include_router(pedidos.router)
app.include_router(reportes.router)


@app.get("/", tags=["Inicio"])
def inicio() -> dict[str, str]:
    return {"mensaje": "API de la tienda ADSO", "documentacion": "/docs"}
