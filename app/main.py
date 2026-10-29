from fastapi import FastAPI

from app.routers import clientes, productos

app = FastAPI(title="Taller 3 ADSO - Tienda")
app.include_router(clientes.router)
app.include_router(productos.router)


@app.get("/")
def inicio() -> dict[str, str]:
    return {"mensaje": "API de la tienda ADSO", "documentacion": "/docs"}
