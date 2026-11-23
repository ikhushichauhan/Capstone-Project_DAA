"""Helpers shared by every knapsack algorithm."""


def ratio(item):
    """Profit-to-weight ratio (profit earned per kg of storage)."""
    return item["profit"] / item["weight"]


def sorted_by_ratio(items):
    """Items sorted by profit/weight, best first (ties: lighter item first)."""
    return sorted(items, key=lambda it: (-ratio(it), it["weight"], it["id"]))


def build_result(key, name, capacity, chosen, steps, elapsed_ms, complexity):
    """Turn a list of (item, fraction) pairs into the JSON-friendly result dict.

    fraction = 1.0 means the whole item was stored, 0 < fraction < 1 means only
    part of it (possible in the fractional knapsack only).
    """
    selected = []
    total_profit = 0.0
    total_weight = 0.0

    for item, fraction in chosen:
        taken = item["weight"] * fraction
        earned = item["profit"] * fraction
        total_weight += taken
        total_profit += earned
        selected.append({
            "id": item["id"],
            "name": item["name"],
            "category": item.get("category", ""),
            "weight": item["weight"],
            "profit": item["profit"],
            "ratio": round(ratio(item), 2),
            "fraction": round(fraction, 4),
            "taken_weight": round(taken, 2),
            "earned": round(earned, 2),
        })

    return {
        "key": key,
        "name": name,
        "capacity": capacity,
        "total_profit": round(total_profit, 2),
        "total_weight": round(total_weight, 2),
        "remaining": round(capacity - total_weight, 2),
        "utilization": round(100 * total_weight / capacity, 1) if capacity else 0.0,
        "items_selected": len(selected),
        "full_items": sum(1 for s in selected if s["fraction"] >= 0.9999),
        "partial_items": sum(1 for s in selected if s["fraction"] < 0.9999),
        "selected": selected,
        "steps": steps,
        "time_ms": round(elapsed_ms, 4),
        "complexity": complexity,
    }
