-- Ejecutar una sola vez en una base nueva para evitar duplicar registros.
USE tienda_adso;

INSERT INTO clientes (nombre, correo) VALUES
  ('Ana Pérez', 'ana@example.com'),
  ('Carlos Ruiz', 'carlos@example.com');

INSERT INTO productos (nombre, precio, stock) VALUES
  ('Mouse', 35000.00, 12),
  ('Teclado', 80000.00, 8),
  ('Monitor', 650000.00, 4);
