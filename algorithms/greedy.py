"""Greedy approaches to the knapsack problem.

Greedy choice: always pick the item with the highest profit/weight ratio next.

* fractional_knapsack  - items may be split. This is OPTIMAL for the fractional
                         problem (and an upper bound for the 0/1 problem).
* greedy_whole_knapsack - same ordering but items cannot be split. Fast, but NOT
                         guaranteed optimal for 0/1 (shown for comparison).

Time complexity: O(n log n) because of the sort, the selection loop is O(n).
Space complexity: O(n).
"""
import time

from .common import build_result, ratio, sorted_by_ratio


def fractional_knapsack(items, capacity, trace=True):
    """Greedy Fractional Knapsack.

    1. Sort items by profit/weight (descending).
    2. Take whole items while they fit.
    3. Take the needed fraction of the first item that does not fit, then stop.
    """
    start = time.perf_counter()
    remaining = float(capacity)
    chosen, steps = [], []

    for rank, item in enumerate(sorted_by_ratio(items), start=1):
        before = remaining

        if remaining <= 0:
            fraction, action, reason = 0.0, "skip", "Knapsack is already full"
        elif item["weight"] <= remaining:
            fraction, action, reason = 1.0, "full", "Fits completely"
        else:
            fraction = remaining / item["weight"]
            action = "partial"
            reason = f"Only {fraction * 100:.1f}% fits, so a fraction is taken"

        if fraction > 0:
            chosen.append((item, fraction))
            remaining = 0.0 if fraction < 1 else remaining - item["weight"]

        if trace:
            steps.append({
                "rank": rank,
                "id": item["id"],
                "name": item["name"],
                "weight": item["weight"],
                "profit": item["profit"],
                "ratio": round(ratio(item), 2),
                "remaining_before": round(before, 2),
                "action": action,
                "fraction": round(fraction, 4),
                "reason": reason,
            })

    elapsed = (time.perf_counter() - start) * 1000
    return build_result("fractional", "Greedy - Fractional Knapsack", capacity,
                        chosen, steps, elapsed, "O(n log n)")


def greedy_whole_knapsack(items, capacity, trace=True):
    """Greedy for whole items: ratio order, skip anything that does not fit."""
    start = time.perf_counter()
    remaining = float(capacity)
    chosen, steps = [], []

    for rank, item in enumerate(sorted_by_ratio(items), start=1):
        before = remaining

        if item["weight"] <= remaining:
            fraction, action, reason = 1.0, "full", "Fits completely"
            chosen.append((item, 1.0))
            remaining -= item["weight"]
        else:
            fraction, action = 0.0, "skip"
            reason = ("Knapsack is already full" if remaining <= 0
                      else "Too heavy for the remaining space")

        if trace:
            steps.append({
                "rank": rank,
                "id": item["id"],
                "name": item["name"],
                "weight": item["weight"],
                "profit": item["profit"],
                "ratio": round(ratio(item), 2),
                "remaining_before": round(before, 2),
                "action": action,
                "fraction": fraction,
                "reason": reason,
            })

    elapsed = (time.perf_counter() - start) * 1000
    return build_result("greedy_whole", "Greedy - Whole Items Only", capacity,
                        chosen, steps, elapsed, "O(n log n)")
