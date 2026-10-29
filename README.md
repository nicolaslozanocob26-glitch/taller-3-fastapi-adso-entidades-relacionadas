# Taller práctico 3 ADSO

API REST para administrar clientes, productos y pedidos de una tienda de tecnología. La solución usa FastAPI y MySQL, separa los routers por recurso y procesa cada pedido en una transacción que guarda el encabezado, sus detalles y el descuento de inventario como una sola operación.

## Modelo relacional

- Un cliente puede tener muchos pedidos; cada pedido referencia un cliente mediante `cliente_id`.
- Un pedido tiene uno o más renglones en `detalle_pedidos`.
- Un producto puede aparecer en los detalles de varios pedidos.
- `detalle_pedidos` resuelve la relación muchos a muchos entre pedidos y productos. Guarda cantidad y una copia del precio al momento de la compra.
- Las claves foráneas impiden que queden pedidos sin cliente o detalles sin pedido o producto.

## Requisitos

- Python 3.10 o posterior.
- MySQL 8 o MariaDB con InnoDB.
- Una cuenta de aplicación con permisos `SELECT`, `INSERT`, `UPDATE` y `DELETE` en `tienda_adso`.

No se necesita reinstalar MySQL ni XAMPP. La guía asume que el servidor está instalado y disponible.

## Preparar MySQL

1. Abra MySQL Workbench o phpMyAdmin con una cuenta administrativa.
2. Ejecute `sql/01_esquema.sql`.
3. Ejecute `sql/02_datos_prueba.sql` una sola vez en una base nueva.
4. Ejecute `sql/03_permisos_api.sql`. Si `api_adso` aún no existe, cree esa cuenta con una clave propia antes de ejecutar el `GRANT`.
5. Verifique que haya dos clientes y tres productos:

```sql
SELECT * FROM tienda_adso.clientes;
SELECT * FROM tienda_adso.productos;
```

## Instalar y ejecutar

En PowerShell, desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `.env` con la clave local de la cuenta `api_adso`. No use `root` en este archivo y no comparta `.env`.

```powershell
fastapi dev app/main.py
```

Abra <http://127.0.0.1:8000/docs>. `GET /` muestra el estado inicial de la API y `GET /docs` contiene la interfaz Swagger.

## Endpoints

| Método | Ruta | Resultado |
| --- | --- | --- |
| GET | `/clientes` | Lista clientes |
| GET | `/clientes/{id}` | Consulta un cliente |
| POST | `/clientes` | Registra un cliente; correo duplicado: 409 |
| PUT | `/clientes/{id}` | Actualiza nombre y correo |
| DELETE | `/clientes/{id}` | Elimina solo si no tiene pedidos; de lo contrario: 409 |
| GET | `/clientes/{id}/pedidos` | Reto A: pedidos del cliente con JOIN |
| GET | `/productos` | Lista y pagina; acepta `buscar`, `pagina` y `limite` |
| GET | `/productos/{id}` | Consulta un producto |
| POST | `/productos` | Registra un producto con precio positivo y stock no negativo |
| PATCH | `/productos/{id}/stock?stock=10` | Cambia el stock disponible |
| POST | `/pedidos` | Crea pedido, detalles y descuenta inventario en una transacción |
| GET | `/pedidos` | Lista pedidos con el nombre del cliente |
| GET | `/pedidos/{id}` | Consulta el encabezado y sus productos |
| POST | `/pedidos/{id}/cancelar` | Reto D: devuelve el stock y cancela una sola vez |
| GET | `/reportes/ventas-por-cliente` | Reto E: total y cantidad de pedidos confirmados por cliente |

FastAPI devuelve `422` ante un cuerpo inválido, `404` cuando falta el registro y `409` para conflictos como correo duplicado o stock insuficiente.

## Ejemplo de pedido

Con los datos iniciales, envíe a `POST /pedidos`:

```json
{
  "cliente_id": 1,
  "items": [
    {"producto_id": 1, "cantidad": 2},
    {"producto_id": 2, "cantidad": 1}
  ]
}
```

El total esperado es **150000.00**: dos Mouse de 35000 y un Teclado de 80000. El stock debe bajar de 12 a 10 Mouse y de 8 a 7 Teclados.

## Cómo se protege el pedido

`app/routers/pedidos.py` bloquea las filas de producto con `SELECT ... FOR UPDATE`, valida la existencia y disponibilidad, calcula el total desde los precios de la base y luego inserta el pedido y sus detalles y descuenta el stock. `app/database.py` confirma al terminar sin errores y hace `ROLLBACK` si una validación o consulta falla. Por eso una cantidad excesiva no deja un pedido parcial ni altera el inventario.

El precio unitario se copia en el detalle. Si el catálogo cambia después, el pedido conserva el precio histórico usado al comprar.

## Respuestas de sustentación

1. **¿Para qué sirve `detalle_pedidos`?** Guarda los productos de cada pedido, con cantidad, precio unitario y subtotal. Permite que un pedido contenga varios productos y que un producto aparezca en distintos pedidos.
2. **¿Por qué se usan claves foráneas?** Mantienen la integridad referencial. Exigen que cada pedido apunte a un cliente existente y que cada detalle apunte a un pedido y un producto existentes.
3. **¿Qué protege una transacción?** La consistencia del pedido completo. El encabezado, los renglones y el descuento de inventario se guardan juntos; ante un error se revierten todos.
4. **¿En qué archivos se separa la lógica?** `main.py` crea la API y registra routers; `database.py` gestiona conexión y transacción; `schemas.py` valida solicitudes; cada archivo de `app/routers/` implementa un recurso; `sql/` crea y prepara la base.

## Retos incluidos

- A: historial de pedidos por cliente con JOIN.
- B: enumera estados `pendiente`, `confirmado` y `cancelado`; los pedidos nuevos quedan confirmados y solo se permite cancelar una vez un pedido confirmado.
- C: `PUT` y `DELETE` para clientes; un cliente con pedidos devuelve `409`.
- D: la cancelación bloquea las filas, devuelve las cantidades y cambia el estado dentro de la misma transacción.
- E: reporte por cliente con `COUNT`, `SUM`, `LEFT JOIN` y exclusión de pedidos cancelados.

## Pruebas y evidencias

La carpeta `evidencias/` reúne las capturas de Swagger, SQL, inventario y persistencia. Se verificaron 28 casos contra MySQL 8.0.46: todos coincidieron con el código HTTP esperado. Los casos principales también se ejecutaron en Swagger y quedaron capturados.

- El pedido de ejemplo devolvió `201`, con total `150000.00`; el stock pasó de 12 a 10 Mouse y de 8 a 7 Teclados.
- Una cantidad superior al inventario devolvió `409`. Se comprobó que no apareció otro pedido y que el inventario no cambió.
- Un cliente inexistente devolvió `404`; un correo duplicado, `409`; un precio negativo, `422`.
- La cancelación devolvió las unidades al inventario y una segunda cancelación devolvió `409`.
- Después de reiniciar Uvicorn, `GET /pedidos/1` recuperó desde MySQL el mismo pedido confirmado.

`evidencias/matriz_pruebas.json` registra los 28 casos; `resultados_swagger_errores.json` conserva las respuestas de error observadas en Swagger. `INFORME_TALLER.md` explica el modelo, las transacciones y las respuestas de sustentación.

La imagen `01_estructura_proyecto.png` es un árbol del directorio real generado a partir de sus archivos; no es una captura de la ventana de VS Code.

La persistencia se demuestra reiniciando solo FastAPI: los datos permanecen en MySQL. No borre la base entre la creación del pedido y esa comprobación.

## Estructura

```text
app/                 API, esquemas, conexión y routers
sql/                 esquema, datos de ejemplo y permisos de aplicación
evidencias/          capturas de las pruebas ejecutadas
requirements.txt     dependencias Python
.env.example         plantilla sin credenciales reales
INFORME_TALLER.md    análisis, matriz y respuestas de sustentación
```
