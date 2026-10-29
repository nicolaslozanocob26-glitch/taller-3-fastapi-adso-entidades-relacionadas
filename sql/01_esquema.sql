-- Ejecutar en MySQL Workbench o phpMyAdmin con una cuenta administrativa.
CREATE DATABASE IF NOT EXISTS tienda_adso
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tienda_adso;

CREATE TABLE IF NOT EXISTS clientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  correo VARCHAR(120) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS productos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  precio DECIMAL(12,2) NOT NULL,
  stock INT NOT NULL DEFAULT 0,
  CONSTRAINT chk_productos_precio CHECK (precio > 0),
  CONSTRAINT chk_productos_stock CHECK (stock >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pedidos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado ENUM('pendiente', 'confirmado', 'cancelado') NOT NULL DEFAULT 'confirmado',
  total DECIMAL(12,2) NOT NULL DEFAULT 0,
  CONSTRAINT fk_pedido_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS detalle_pedidos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  pedido_id INT NOT NULL,
  producto_id INT NOT NULL,
  cantidad INT NOT NULL,
  precio_unitario DECIMAL(12,2) NOT NULL,
  subtotal DECIMAL(12,2) NOT NULL,
  CONSTRAINT chk_detalle_cantidad CHECK (cantidad > 0),
  CONSTRAINT fk_detalle_pedido FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
  CONSTRAINT fk_detalle_producto FOREIGN KEY (producto_id) REFERENCES productos(id),
  CONSTRAINT uq_pedido_producto UNIQUE (pedido_id, producto_id)
) ENGINE=InnoDB;
