from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class Product:
    codigo: str
    nombre: str
    categoria: Optional[str] = ""
    precio: float = 0.0
    cantidad: int = 0
    avg_cost: float = 0.0

    def __post_init__(self):
        self.codigo = str(self.codigo).strip()
        self.nombre = str(self.nombre).strip()
        self.categoria = str(self.categoria or "").strip()
        self.precio = float(self.precio or 0.0)
        self.cantidad = int(self.cantidad or 0)
        self.avg_cost = float(self.avg_cost or self.precio)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_db_row(cls, row) -> "Product":
        # row: (codigo,nombre,categoria,precio,cantidad,avg_cost)
        return cls(codigo=row[0], nombre=row[1], categoria=row[2], precio=row[3], cantidad=row[4], avg_cost=row[5] if len(row)>5 else 0.0)
