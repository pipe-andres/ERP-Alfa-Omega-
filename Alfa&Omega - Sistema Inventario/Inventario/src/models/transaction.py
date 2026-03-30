from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

@dataclass
class TransactionLine:
    codigo: str
    qty: float
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Transaction:
    id: Optional[int]
    tipo: str
    numero: Optional[str]
    fecha: Optional[str]
    partner_id: Optional[int]
    lines: Optional[List[TransactionLine]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d
