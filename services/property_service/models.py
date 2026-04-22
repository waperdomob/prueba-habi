"""Modelos de dominio del Servicio 1."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PropertyStatus(str, Enum):
    """Estados visibles para el usuario externo.

    Cualquier estado fuera de este enum nunca debe exponerse en la API,
    conforme a la regla de negocio del Servicio 1.
    """

    PRE_VENTA = "pre_venta"
    EN_VENTA = "en_venta"
    VENDIDO = "vendido"

    @classmethod
    def values(cls) -> list[str]:
        return [s.value for s in cls]

    @classmethod
    def from_value(cls, value: str) -> "PropertyStatus":
        """Convierte un string a PropertyStatus. Lanza ValueError si no es válido."""
        try:
            return cls(value)
        except ValueError:
            raise ValueError(
                f"Estado '{value}' no es válido. "
                f"Valores permitidos: {cls.values()}"
            )


@dataclass(frozen=True)
class PropertyFilters:
    """Filtros aceptados por el endpoint de consulta.

    Todos los campos son opcionales. Si ninguno se proporciona, se listan
    todos los inmuebles visibles (con paginación por defecto).
    """

    year: Optional[int] = None
    city: Optional[str] = None
    status: Optional[PropertyStatus] = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class Property:
    """Representación de un inmueble tal como se expone al usuario."""

    address: str
    city: str
    status: str
    price: Optional[int]
    description: Optional[str]

    def to_dict(self) -> dict:
        return {
            "address": self.address,
            "city": self.city,
            "status": self.status,
            "price": self.price,
            "description": self.description,
        }
