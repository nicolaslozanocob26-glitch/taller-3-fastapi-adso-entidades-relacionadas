# Informe del taller práctico 3

## Resultado

Se implementó y ejecutó una API REST modular con FastAPI y MySQL 8.0.46. La venta de ejemplo registró un total de **150000.00**; el pedido, sus detalles y la reducción de inventario quedaron guardados juntos. Se verificaron **28 casos**, todos con el resultado esperado.

## Modelo de datos

`clientes` y `pedidos` tienen relación uno a muchos mediante `pedidos.cliente_id`. Un pedido contiene uno o varios artículos en `detalle_pedidos`. Esta tabla resuelve la relación muchos a muchos entre pedidos y productos; además guarda cantidad, precio unitario y subtotal. El precio se conserva como una copia histórica para que los cambios futuros del catálogo no alteren ventas pasadas.

Las claves foráneas impiden asociar un pedido con un cliente inexistente o un detalle con un pedido o producto inexistente. InnoDB aplica las claves y proporciona transacciones. Los campos monetarios usan `DECIMAL(12,2)`.

## Organización de la aplicación

`app/main.py` crea la API y registra los routers. `app/database.py` centraliza la conexión PyMySQL y el `COMMIT` o `ROLLBACK`. `app/schemas.py` valida los cuerpos recibidos. `app/routers/clientes.py`, `productos.py`, `pedidos.py` y `reportes.py` separan los endpoints por recurso. `sql/` contiene el esquema, los datos de ejemplo y los permisos de la cuenta de aplicación.

## Transacción de pedidos

Al crear un pedido, la API comprueba el cliente, bloquea los productos con `SELECT ... FOR UPDATE`, valida el stock, calcula cada subtotal desde el precio guardado en MySQL, inserta el encabezado y los detalles y descuenta las unidades. Todo ocurre en una única transacción. Si falla una comprobación, el contexto de `app/database.py` hace rollback.

En la prueba con stock excesivo, Swagger devolvió `409`. Después se volvió a consultar el inventario: los Mouse permanecieron en 10 y los Teclados en 7; no se creó otro pedido. La cancelación usa otra transacción, devuelve las unidades y cambia el estado una sola vez.

## Matriz resumida de resultados

| Caso | Resultado esperado | Resultado obtenido |
| --- | --- | --- |
| Listar clientes y productos | 200 | 200 |
| Crear cliente y producto | 201 | 201 |
| Correo duplicado | 409 | 409 |
| Precio negativo | 422 | 422 |
| Actualizar cliente y stock | 200 | 200 |
| Eliminar cliente sin pedidos | 204 | 204 |
| Eliminar cliente con pedidos | 409 | 409 |
| Crear pedido válido | 201 y total 150000.00 | 201 y total 150000.00 |
| Pedido con cliente inexistente | 404, sin cambios | 404, sin cambios |
| Pedido por encima del stock | 409, sin pedido parcial | 409, sin pedido parcial |
| Ver pedido con detalles | 200 | 200 |
| Pedidos por cliente y reporte | 200 | 200 |
| Cancelar y devolver stock | 200 y stock restaurado | 200 y stock restaurado |
| Cancelar otra vez | 409, sin devolverlo de nuevo | 409, sin devolverlo de nuevo |
| Reiniciar FastAPI y consultar pedido 1 | 200, pedido persistente | 200, pedido persistente |

El detalle de los 28 casos está en `evidencias/matriz_pruebas.json`. Los errores duplicado, precio inválido y cliente inexistente también tienen respuestas capturadas desde Swagger en `evidencias/resultados_swagger_errores.json`.

## Evidencias incluidas

| Archivo | Evidencia |
| --- | --- |
| `01_estructura_proyecto.png` | Árbol de archivos del proyecto |
| `02_swagger_recursos.png` | Endpoints documentados por recurso |
| `03_stock_inicial.png` | Inventario antes de la compra |
| `04_pedido_exitoso.png` | `POST /pedidos`, estado 201 y total |
| `05_detalle_pedido.png` | Encabezado y renglones del pedido |
| `06_stock_despues.png` | Inventario tras la compra |
| `07_rollback_stock_excesivo.png` | Respuesta 409 para stock insuficiente |
| `08_persistencia_reinicio.png` | Pedido consultado después de reiniciar Uvicorn |
| `09_consulta_join_sql.png` | Consulta JOIN ejecutada en MySQL y filas obtenidas |
| `10_correo_duplicado.png` | Respuesta 409 |
| `11_precio_invalido.png` | Respuesta 422 |
| `12_cliente_inexistente.png` | Respuesta 404 |
| `13_stock_sin_cambios.png` | Inventario consultado después de los errores |

La imagen `01_estructura_proyecto.png` se generó leyendo la carpeta del proyecto; representa su árbol real de archivos. No es una captura tomada dentro de VS Code.

## Respuestas para la sustentación

1. **¿Para qué sirve `detalle_pedidos`?** Guarda cada producto incluido en un pedido, con cantidad, precio unitario y subtotal. Permite relacionar varios productos con varios pedidos.
2. **¿Por qué se usan claves foráneas?** Para mantener la integridad referencial y evitar pedidos sin cliente o detalles vinculados a productos inexistentes.
3. **¿Qué protege una transacción?** La consistencia del pedido completo. Encabezado, detalles y descuentos de stock se confirman juntos o se revierten juntos.
4. **¿En qué archivos se separa la lógica?** `main.py` registra routers, `database.py` gestiona conexión y transacciones, `schemas.py` valida datos, `app/routers/` implementa recursos y `sql/` crea y prepara las tablas.
