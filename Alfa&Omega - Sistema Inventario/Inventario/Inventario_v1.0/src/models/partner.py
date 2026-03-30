from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class Partner:
    id: Optional[int]
    code: str
    kind: Optional[str] = None
    name: Optional[str] = None
    tax_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

    def __post_init__(self):
        self.code = str(self.code)
        self.name = str(self.name) if self.name is not None else None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
