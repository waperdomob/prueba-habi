"""Excepciones de dominio del Servicio 1.

Estas excepciones permiten al controller mapear cada caso a un código HTTP
apropiado sin que el use case o el repository conozcan HTTP.
"""


class PropertyServiceError(Exception):
    """Base de todas las excepciones del servicio."""


class InvalidFilterError(PropertyServiceError):
    """El cliente envió un filtro con formato o valor inválido.

    Se mapea a HTTP 400.
    """


class RepositoryError(PropertyServiceError):
    """Error al consultar la base de datos.

    Se mapea a HTTP 500. El detalle se loguea pero no se expone al cliente.
    """
