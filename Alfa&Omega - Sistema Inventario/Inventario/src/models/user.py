from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

@dataclass
class User:
    id: Optional[int]
    username: str
    name: Optional[str] = None
    active: bool = True
    roles: Optional[List[str]] = None

    def __post_init__(self):
        self.username = str(self.username)
        self.name = str(self.name) if self.name is not None else None
        self.active = bool(self.active)
        self.roles = list(self.roles) if self.roles else []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
