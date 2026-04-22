"""Carga y valida la configuración de la aplicación desde variables de entorno."""

import os
from dataclasses import dataclass


def _read_env_file(path: str = ".env") -> None:
    """Lee un archivo .env simple y lo carga en os.environ si existe.

    Implementación mínima para evitar la dependencia de python-dotenv.
    No soporta comillas complejas ni interpolación, que no son necesarias aquí.
    """
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # No sobrescribir variables ya definidas en el entorno
            if key and key not in os.environ:
                os.environ[key] = value


_read_env_file()


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass(frozen=True)
class ServerSettings:
    host: str
    port: int


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"La variable de entorno '{name}' es obligatoria. "
            f"Revisa tu archivo .env (ver .env.example)."
        )
    return value


def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings(
        host=_require("DB_HOST"),
        port=int(os.environ.get("DB_PORT", "3309")),
        user=_require("DB_USER"),
        password=_require("DB_PASSWORD"),
        database=_require("DB_NAME"),
    )


def get_server_settings() -> ServerSettings:
    return ServerSettings(
        host=os.environ.get("HTTP_HOST", "0.0.0.0"),
        port=int(os.environ.get("HTTP_PORT", "8000")),
    )


def get_log_level() -> str:
    return os.environ.get("LOG_LEVEL", "INFO").upper()
