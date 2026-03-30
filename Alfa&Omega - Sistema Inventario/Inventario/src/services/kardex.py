"""Kardex profesional: soporte FIFO, LIFO y AVG (promedio ponderado).

Provee `get_product_kardex(product_code, warehouse_id=None)` que devuelve una lista
de movimientos con costes calculados según la política indicada en la env var
`INVENTORY_COST_POLICY` (por defecto 'fifo').
"""
from __future__ import annotations
from typing import List, Dict, Optional
import os

from src.database import repository


def _policy() -> str:
    return os.getenv("INVENTORY_COST_POLICY", "fifo").lower()


def get_product_kardex(product_code: str, warehouse_id: Optional[int] = None) -> List[Dict]:
    """Return computed kardex movements for a product according to policy.

    Each movement dict contains: date, type, qty, unit_cost, total_cost, balance_qty, balance_cost
    """
    moves = repository.get_kardex_moves(product_code, warehouse_id)
    # moves are tuples from DB; map to dict for convenience (index positions may vary)
    mapped = []
    for r in moves:
        # assume order of columns as inserted in repository.record_kardex_move
        mapped.append({
            "id": r[0], "product_code": r[1], "type": r[2], "qty": float(r[3] or 0),
            "unit_cost": r[4], "total_cost": r[5], "balance_qty": r[6], "balance_cost": r[7],
            "balance_total": r[8], "date": r[9], "warehouse_id": r[10], "ref_type": r[11], "ref_id": r[12]
        })

    policy = _policy()

    # layer stack for FIFO/LIFO: list of [qty_remaining, unit_cost]
    layers: List[List[float]] = []
    results: List[Dict] = []

    def total_layers():
        tq = sum(l[0] for l in layers)
        tc = sum(l[0] * l[1] for l in layers)
        return tq, (tc / tq if tq else 0.0), tc

    for m in mapped:
        t = m["type"].upper()
        qty = float(m["qty"])
        unit_cost = float(m["unit_cost"] or 0.0)

        if t in ("IN", "PURCHASE", "ADJUST+", "TRANSFER_IN"):
            # add layer
            layers.append([qty, unit_cost])
            tq, avg, tc = total_layers()
            results.append({**m, "computed_unit_cost": unit_cost, "computed_total_cost": qty * unit_cost, "balance_qty": tq, "balance_cost": avg})

        elif t in ("OUT", "SALE", "ADJUST-", "TRANSFER_OUT"):
            needed = abs(qty)
            moved_cost = 0.0
            if policy == "avg":
                tq, avg, tc = total_layers()
                cost_per_unit = avg
                moved_cost = needed * cost_per_unit
                # remove proportionally from layers
                remaining = needed
                # reduce layers starting from oldest (FIFO behavior for depletion)
                i = 0
                while remaining > 1e-9 and i < len(layers):
                    take = min(remaining, layers[i][0])
                    layers[i][0] -= take
                    remaining -= take
                    if layers[i][0] <= 1e-9:
                        i += 1
                # drop empty layers
                layers[:] = [l for l in layers if l[0] > 1e-9]
                tq2, avg2, tc2 = total_layers()
                results.append({**m, "computed_unit_cost": cost_per_unit, "computed_total_cost": moved_cost, "balance_qty": tq2, "balance_cost": avg2})
            else:
                # FIFO: consume from start; LIFO: consume from end
                remaining = needed
                if policy == "lifo":
                    consume_order = list(range(len(layers) - 1, -1, -1))
                else:
                    consume_order = list(range(len(layers)))

                for idx in consume_order:
                    if remaining <= 1e-9:
                        break
                    if layers[idx][0] <= 1e-9:
                        continue
                    take = min(layers[idx][0], remaining)
                    moved_cost += take * layers[idx][1]
                    layers[idx][0] -= take
                    remaining -= take
                # cleanup empty layers
                layers[:] = [l for l in layers if l[0] > 1e-9]
                tq2, avg2, tc2 = total_layers()
                if remaining > 1e-9:
                    # stock insuficiente en capas — registrar advertencia pero continuar
                    import logging
                    logging.getLogger(__name__).warning(
                        f"Kardex: stock insuficiente para '{product_code}' en {m.get('date')} "
                        f"(faltaron {remaining:.4f} unidades)"
                    )
                unit_cost_effective = (moved_cost / needed) if needed else 0.0
                results.append({**m, "computed_unit_cost": unit_cost_effective, "computed_total_cost": moved_cost, "balance_qty": tq2, "balance_cost": avg2})
        else:
            # unknown type -> copy
            tq, avg, tc = total_layers()
            results.append({**m, "computed_unit_cost": unit_cost, "computed_total_cost": qty * unit_cost, "balance_qty": tq, "balance_cost": avg})

    return results