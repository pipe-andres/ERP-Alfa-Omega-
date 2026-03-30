import os
import json
from typing import Any, Callable, Dict, List

# simple JSON-backed persistence for "tables" stored under DATA_DIR
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.getenv("DB_JSON_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)


def _filepath(table: str) -> str:
    return os.path.join(DATA_DIR, f"{table}.json")


def load_table(table: str) -> List[Dict[str, Any]]:
    try:
        with open(_filepath(table), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_table(table: str, rows: List[Dict[str, Any]]) -> None:
    with open(_filepath(table), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)


def find_one(table: str, predicate: Callable[[Dict[str, Any]], bool]) -> Dict[str, Any] | None:
    for r in load_table(table):
        if predicate(r):
            return r
    return None


def insert(table: str, record: Dict[str, Any]) -> None:
    rows = load_table(table)
    rows.append(record)
    save_table(table, rows)


def update(table: str, predicate: Callable[[Dict[str, Any]], bool], updater: Callable[[Dict[str, Any]], None]) -> bool:
    rows = load_table(table)
    modified = False
    for r in rows:
        if predicate(r):
            updater(r)
            modified = True
    if modified:
        save_table(table, rows)
    return modified


def delete(table: str, predicate: Callable[[Dict[str, Any]], bool]) -> bool:
    rows = load_table(table)
    new_rows = [r for r in rows if not predicate(r)]
    if len(new_rows) != len(rows):
        save_table(table, new_rows)
        return True
    return False


def count(table: str, predicate: Callable[[Dict[str, Any]], bool] = lambda r: True) -> int:
    return sum(1 for r in load_table(table) if predicate(r))


def get_next_id(table: str) -> int:
    """Get next available numeric ID for a table."""
    rows = load_table(table)
    if not rows:
        return 1
    max_id = max(int(r.get('id', 0)) for r in rows if isinstance(r.get('id'), (int, str)) and str(r.get('id')).isdigit())
    return max_id + 1


def list_rows(table: str,
              predicate: Callable[[Dict[str, Any]], bool] = lambda r: True,
              order_key: str | None = None,
              limit: int | None = None,
              offset: int = 0) -> List[Dict[str, Any]]:
    rows = [r for r in load_table(table) if predicate(r)]
    if order_key:
        rows.sort(key=lambda x: (x.get(order_key) is None, x.get(order_key)))
    if offset:
        rows = rows[offset:]
    if limit is not None:
        rows = rows[:limit]
    return rows
