-- Ejecutar como administrador después de crear tienda_adso.
-- Si api_adso ya existe, este GRANT conserva su contraseña actual.
GRANT SELECT, INSERT, UPDATE, DELETE ON tienda_adso.*
TO 'api_adso'@'127.0.0.1';
FLUSH PRIVILEGES;

-- Si la cuenta no existe, crearla antes con una clave propia:
-- CREATE USER 'api_adso'@'127.0.0.1' IDENTIFIED BY 'CLAVE_LOCAL_SEGURA';
