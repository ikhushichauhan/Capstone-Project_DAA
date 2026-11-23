"""Performance benchmark: Greedy vs Dynamic Programming on random inventories."""
import random

from .dynamic import dp_knapsack
from .greedy import fractional_knapsack, greedy_whole_knapsack

MAX_ITEMS = 500


def generate_items(n, seed=42):
    """Reproducible random inventory: weight 1-20 kg, profit 10-100."""
    rng = random.Random(seed + n)
    return [
        {
            "id": i + 1,
            "name": f"Item {i + 1}",
            "weight": rng.randint(1, 20),
            "profit": rng.randint(10, 100),
        }
        for i in range(n)
    ]


def _best_of(fn, repeats):
    """Run fn several times, keep the result and the fastest time (least noise)."""
    best_ms, result = None, None
    for _ in range(repeats):
        result = fn()
        if best_ms is None or result["time_ms"] < best_ms:
            best_ms = result["time_ms"]
    return result, best_ms


def run_benchmark(sizes, repeats=3, seed=42):
    rows = []
    for n in sizes:
        items = generate_items(n, seed)
        # Capacity = half of the total stock weight, a realistic "tight" warehouse.
        capacity = max(1, sum(i["weight"] for i in items) // 2)

        frac, frac_ms = _best_of(
            lambda: fractional_knapsack(items, capacity, trace=False), repeats)
        whole, whole_ms = _best_of(
            lambda: greedy_whole_knapsack(items, capacity, trace=False), repeats)
        dp, dp_ms = _best_of(
            lambda: dp_knapsack(items, capacity, trace=False), repeats)

        rows.append({
            "n": n,
            "capacity": capacity,
            "dp_cells": n * (capacity + 1),
            "fractional_ms": frac_ms,
            "greedy_whole_ms": whole_ms,
            "dp_ms": dp_ms,
            "fractional_profit": frac["total_profit"],
            "greedy_whole_profit": whole["total_profit"],
            "dp_profit": dp["total_profit"],
            "speedup": round(dp_ms / max(frac_ms, 1e-6), 1),
        })
    return rows
