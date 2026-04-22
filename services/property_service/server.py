"""Servidor HTTP del Servicio 1.

Usa la librería estándar de Python (http.server + socketserver) conforme al
requisito de no usar frameworks. ThreadingHTTPServer permite atender varias
requests en paralelo sin bloquear.

Ejecución:
    python -m services.property_service.server
"""

import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from config.settings import get_log_level, get_server_settings
from services.property_service.controllers import PropertyController, Response
from services.property_service.repository import PropertyRepository
from services.property_service.router import RouteContext, Router
from services.property_service.use_cases import ListVisiblePropertiesUseCase

logger = logging.getLogger(__name__)


# CORS mínimo: el frontend (Extra 2) se sirve desde un origen distinto
# (file:// o http://localhost:xxxx) y necesita poder hacer fetch.
# En producción se configuraría un dominio específico; para la prueba,
# permitir cualquier origen es aceptable y está documentado.
_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def _build_router() -> Router:
    """Construye el grafo de dependencias del servicio."""
    repository = PropertyRepository()
    use_case = ListVisiblePropertiesUseCase(repository=repository)
    controller = PropertyController(use_case=use_case)
    return Router(property_controller=controller)


class PropertyRequestHandler(BaseHTTPRequestHandler):
    # Compartido por todos los handlers; se inyecta en ``main()``.
    router: Router = None  # type: ignore[assignment]

    # --- overrides HTTP ---

    def do_GET(self) -> None:  # noqa: N802 — firma impuesta por la base class
        self._dispatch("GET")

    def do_OPTIONS(self) -> None:  # noqa: N802
        # Responder preflights de CORS.
        self.send_response(204)
        for header, value in _CORS_HEADERS.items():
            self.send_header(header, value)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        """Redirige el logging por defecto al logger estándar."""
        logger.info("%s - %s", self.address_string(), format % args)

    # --- dispatch ---

    def _dispatch(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query, keep_blank_values=False)

        handler = self.router.resolve(method, path)
        if handler is None:
            self._send_response(
                Response(
                    status=404,
                    body={"error": "not_found", "message": f"Ruta no encontrada: {method} {path}"},
                )
            )
            return

        content_length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(content_length) if content_length > 0 else b""

        try:
            response = handler(RouteContext(query_params=query_params, body=body))
        except Exception as exc:  # defensa en profundidad: último backstop
            logger.exception("Error no controlado procesando %s %s: %s", method, path, exc)
            response = Response(
                status=500,
                body={"error": "internal_error", "message": "Error interno del servidor"},
            )

        self._send_response(response)

    def _send_response(self, response: Response) -> None:
        payload = response.to_json_bytes()
        self.send_response(response.status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        for header, value in _CORS_HEADERS.items():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    logging.basicConfig(
        level=get_log_level(),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    settings = get_server_settings()
    PropertyRequestHandler.router = _build_router()

    logger.info("Iniciando Property Service en %s:%s", settings.host, settings.port)
    server = ThreadingHTTPServer((settings.host, settings.port), PropertyRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Apagando servidor...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
