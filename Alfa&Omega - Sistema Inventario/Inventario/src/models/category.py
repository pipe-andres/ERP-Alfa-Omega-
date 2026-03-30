from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

@dataclass
class Category:
    id: Optional[int]
    parent_id: Optional[int]
    name: str
    slug: Optional[str] = None
    children: Optional[List["Category"]] = None

    def __post_init__(self):
        self.name = str(self.name)
        self.slug = str(self.slug) if self.slug is not None else None
        self.children = self.children or []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
