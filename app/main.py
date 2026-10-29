from fastapi import FastAPI

app = FastAPI(title="Taller 3 ADSO")


@app.get("/")
def inicio() -> dict[str, str]:
    return {"mensaje": "API en preparación"}
