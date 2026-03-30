from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class Settings:
    company_name: Optional[str] = None
    company_tax: Optional[str] = None
    company_addr: Optional[str] = None
    tax_included: bool = False
    tax_rate: float = 0.0
    logo_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
