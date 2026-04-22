"""Gestión de la conexión a MySQL.

Se usa una conexión por operación (abierta y cerrada mediante context manager).
Para un servicio de prueba técnica con tráfico acotado, un pool añade complejidad
sin beneficio real; si luego se necesita escalar se puede reemplazar el
context manager por un pool (p.ej. mysql.connector.pooling.MySQLConnectionPool)
sin cambiar el resto de la aplicación.

Nota sobre ``use_pure=True``:
    Se fuerza la implementación en Python puro del driver (en lugar de la
    extensión C) porque ha mostrado mejor estabilidad en Windows y cuando el
    servidor atiende requests en múltiples hilos (ThreadingHTTPServer).
    El costo de rendimiento es despreciable para el volumen de una prueba
    técnica y elimina una clase entera de errores intermitentes como el
    ``2013 Lost connection ... waiting for initial communication packet``.
"""

from contextlib import contextmanager
from typing import Iterator

import mysql.connector
from mysql.connector.connection import MySQLConnection

from config.settings import get_database_settings


@contextmanager
def get_connection() -> Iterator[MySQLConnection]:
    """Abre una conexión a MySQL y garantiza su cierre.

    Uso:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT 1")
    """
    settings = get_database_settings()
    conn: MySQLConnection = mysql.connector.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        database=settings.database,
        # Implementación Python pura — más estable en Windows y bajo threading.
        use_pure=True,
        # Tiempos acotados para que un fallo de red no cuelgue el servidor.
        connection_timeout=10,
    )
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass