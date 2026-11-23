"""Dynamic Programming solution of the 0/1 Knapsack problem.

Let dp[i][c] be the best profit using only the first i items with capacity c.

    dp[0][c] = 0
    dp[i][c] = dp[i-1][c]                                   if w_i > c
    dp[i][c] = max(dp[i-1][c], dp[i-1][c - w_i] + p_i)      if w_i <= c

The answer is dp[n][W]. Walking back from dp[n][W] tells us WHICH items were
used: if dp[i][c] != dp[i-1][c], item i was taken and we move to c - w_i.

Time complexity : O(n * W)   (pseudo-polynomial, W = capacity)
Space complexity: O(n * W)
Weights and capacity must be integers so they can index the table.
"""
import time

from .common import build_result

MAX_DP_CELLS = 4_000_000      # protects the server from huge tables
TABLE_DISPLAY_LIMIT = 3_000   # largest table we send to the browser


def _clean(value):
    """150.0 -> 150, 12.345 -> 12.35 (nicer to display)."""
    value = float(value)
    return int(value) if value.is_integer() else round(value, 2)


def dp_knapsack(items, capacity, return_table=False, trace=True):
    n = len(items)
    W = int(capacity)

    if n * (W + 1) > MAX_DP_CELLS:
        raise ValueError(
            f"DP table would have {n * (W + 1):,} cells (limit {MAX_DP_CELLS:,}). "
            "Reduce the capacity or the number of products."
        )

    start = time.perf_counter()

    # --- 1. Fill the table -------------------------------------------------
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        weight = items[i - 1]["weight"]
        profit = items[i - 1]["profit"]
        prev, cur = dp[i - 1], dp[i]
        for c in range(W + 1):
            best = prev[c]                       # option 1: skip the item
            if weight <= c:                      # option 2: take the item
                with_item = prev[c - weight] + profit
                if with_item > best:
                    best = with_item
            cur[c] = best

    # --- 2. Backtrack to find the chosen items ---------------------------------
    chosen, steps, path = [], [], []
    c = W
    for i in range(n, 0, -1):
        item = items[i - 1]
        taken = dp[i][c] != dp[i - 1][c]
        path.append([i, c, taken])

        if trace:
            if taken:
                reason = (f"Value changes from {_clean(dp[i - 1][c])} to "
                          f"{_clean(dp[i][c])}, so this item is in the best set")
            else:
                reason = "Same value without it, so the item is not needed"
            steps.append({
                "step": n - i + 1,
                "id": item["id"],
                "name": item["name"],
                "weight": item["weight"],
                "profit": item["profit"],
                "capacity_left": c,
                "with_item": _clean(dp[i][c]),
                "without_item": _clean(dp[i - 1][c]),
                "action": "take" if taken else "skip",
                "reason": reason,
            })

        if taken:
            chosen.append((item, 1.0))
            c -= item["weight"]
    path.append([0, c, False])
    chosen.reverse()                              # back to original item order

    elapsed = (time.perf_counter() - start) * 1000

    result = build_result("dp", "Dynamic Programming - 0/1 Knapsack", W,
                          chosen, steps, elapsed, "O(n · W)")
    result["table_cells"] = n * (W + 1)

    # --- 3. Optional table for the UI ---------------------------------------
    result["table"] = None
    if return_table:
        if (n + 1) * (W + 1) <= TABLE_DISPLAY_LIMIT:
            result["table"] = {
                "rows": [[_clean(v) for v in row] for row in dp],
                "labels": [it["name"] for it in items],
                "capacity": W,
                "path": path,
            }
        else:
            result["table_note"] = (
                "The table is too large to display "
                f"({(n + 1) * (W + 1):,} cells). Use fewer products or a smaller "
                "capacity to see it."
            )
    return result
