"""
Intelligent Inventory Management Using Knapsack Optimization
============================================================

Problem:
    A warehouse manager has limited storage capacity and many candidate
    products, each with a weight and a profit. The goal is to choose products
    so that TOTAL PROFIT is maximized without exceeding the capacity.

Algorithms implemented:
    1. Fractional Knapsack (Greedy)        - items may be split, O(n log n)
    2. 0/1 Knapsack (Dynamic Programming)  - take an item whole or not at all, O(n * W)
    3. 0/1 Greedy (bonus)                  - shows where greedy fails on 0/1 problems

Run:
    python inventory_knapsack.py              # interactive menu
    python inventory_knapsack.py demo         # sample warehouse demo
    python inventory_knapsack.py benchmark    # performance comparison
    python inventory_knapsack.py plot         # graph (requires matplotlib)
"""

from __future__ import annotations

import random
import sys
import time
from dataclasses import dataclass, field


# ----------------------------------------------------------------------------
# 1. DATA MODELS
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Product:
    """A single warehouse product."""
    name: str
    weight: int      # storage space required (units)
    profit: int      # expected profit (Rs.)

    @property
    def ratio(self) -> float:
        """Profit per unit of weight; the greedy strategy ranks items by this."""
        return self.profit / self.weight


@dataclass
class Result:
    """Output produced by any of the algorithms."""
    algorithm: str
    # (product, fraction_taken); fraction is always 1.0 for 0/1 approaches
    chosen: list[tuple[Product, float]] = field(default_factory=list)
    total_profit: float = 0.0
    total_weight: float = 0.0
    time_ms: float = 0.0


# ----------------------------------------------------------------------------
# 2. ALGORITHMS
# ----------------------------------------------------------------------------
def fractional_knapsack(products: list[Product], capacity: int) -> Result:
    """
    GREEDY (Fractional Knapsack)
    ----------------------------
    Idea: sort items by profit/weight ratio and fill the knapsack with the best
    ones first. If the last item does not fit completely, take only the
    fraction that fits. For the fractional problem this is always optimal.

    Time: O(n log n)  |  Extra space: O(1)
    """
    start = time.perf_counter()
    result = Result("Greedy (Fractional)")
    remaining = capacity

    for p in sorted(products, key=lambda x: x.ratio, reverse=True):
        if remaining <= 0:
            break
        if p.weight <= remaining:                 # take the whole item
            result.chosen.append((p, 1.0))
            result.total_profit += p.profit
            result.total_weight += p.weight
            remaining -= p.weight
        else:                                     # take only a fraction
            frac = remaining / p.weight
            result.chosen.append((p, frac))
            result.total_profit += p.profit * frac
            result.total_weight += remaining
            remaining = 0

    result.time_ms = (time.perf_counter() - start) * 1000
    return result


def greedy_01_knapsack(products: list[Product], capacity: int) -> Result:
    """
    GREEDY applied to the 0/1 problem (bonus, for comparison only)
    --------------------------------------------------------------
    Sort by ratio, take every item that still fits completely, skip the rest.
    This is very fast but gives NO guarantee of optimality.
    """
    start = time.perf_counter()
    result = Result("Greedy (0/1 whole items)")
    remaining = capacity

    for p in sorted(products, key=lambda x: x.ratio, reverse=True):
        if p.weight <= remaining:
            result.chosen.append((p, 1.0))
            result.total_profit += p.profit
            result.total_weight += p.weight
            remaining -= p.weight

    result.time_ms = (time.perf_counter() - start) * 1000
    return result


def dp_knapsack_01(products: list[Product], capacity: int) -> Result:
    """
    DYNAMIC PROGRAMMING (0/1 Knapsack)
    ----------------------------------
    dp[i][w] = maximum profit using the first i products with capacity w.

        dp[i][w] = dp[i-1][w]                                    (skip item i)
        dp[i][w] = max(dp[i-1][w],
                       dp[i-1][w - wt] + profit)   if wt <= w    (take item i)

    The selected items are recovered by backtracking through the table.
    This always returns the optimal 0/1 solution.

    Time: O(n * W)  |  Space: O(n * W)
    """
    start = time.perf_counter()
    n = len(products)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        wt, pr = products[i - 1].weight, products[i - 1].profit
        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]
            if wt <= w:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - wt] + pr)

    # Backtrack to find which items were selected
    result = Result("DP (0/1 Knapsack)")
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:              # item i-1 was taken
            p = products[i - 1]
            result.chosen.append((p, 1.0))
            result.total_weight += p.weight
            w -= p.weight
    result.chosen.reverse()
    result.total_profit = dp[n][capacity]

    result.time_ms = (time.perf_counter() - start) * 1000
    return result


# ----------------------------------------------------------------------------
# 3. DISPLAY HELPERS
# ----------------------------------------------------------------------------
LINE = "=" * 72


def show_inventory(products: list[Product], capacity: int) -> None:
    print(f"\n{LINE}\n  WAREHOUSE INVENTORY  (Capacity: {capacity} units)\n{LINE}")
    print(f"  {'#':<3}{'Product':<22}{'Weight':>8}{'Profit':>10}{'Profit/Wt':>12}")
    print("  " + "-" * 55)
    for i, p in enumerate(products, 1):
        print(f"  {i:<3}{p.name:<22}{p.weight:>8}{p.profit:>10}{p.ratio:>12.2f}")


def show_result(r: Result, capacity: int) -> None:
    print(f"\n{LINE}\n  {r.algorithm}\n{LINE}")
    for p, frac in r.chosen:
        tag = "FULL" if frac == 1.0 else f"{frac * 100:.1f}% (partial)"
        print(f"  [+] {p.name:<22} wt={p.weight:<5} profit={p.profit:<6} -> {tag}")
    used_pct = r.total_weight / capacity * 100 if capacity else 0
    print("  " + "-" * 60)
    print(f"  Total Profit : Rs. {r.total_profit:,.2f}")
    print(f"  Space Used   : {r.total_weight:.2f} / {capacity}  ({used_pct:.1f}%)")
    print(f"  Time Taken   : {r.time_ms:.4f} ms")


def compare(products: list[Product], capacity: int) -> None:
    """Run all three approaches and compare them side by side."""
    results = [
        fractional_knapsack(products, capacity),
        greedy_01_knapsack(products, capacity),
        dp_knapsack_01(products, capacity),
    ]
    for r in results:
        show_result(r, capacity)

    best_01 = results[2].total_profit
    print(f"\n{LINE}\n  COMPARISON SUMMARY\n{LINE}")
    print(f"  {'Algorithm':<28}{'Profit':>12}{'Space':>10}{'Time(ms)':>12}{'vs DP':>10}")
    print("  " + "-" * 70)
    for r in results:
        gap = (r.total_profit - best_01) / best_01 * 100 if best_01 else 0
        print(f"  {r.algorithm:<28}{r.total_profit:>12,.2f}{r.total_weight:>10.1f}"
              f"{r.time_ms:>12.4f}{gap:>+9.1f}%")

    print("\n  INSIGHTS:")
    print("  * Fractional Greedy always earns >= DP because items can be split,")
    print("    but real warehouse boxes cannot be broken, so it is not practical.")
    print("  * 0/1 Greedy is fast but not guaranteed to be optimal.")
    print("  * DP guarantees the best answer when whole items must be chosen.")


# ----------------------------------------------------------------------------
# 4. SAMPLE DATA + BENCHMARK
# ----------------------------------------------------------------------------
def sample_products() -> list[Product]:
    data = [
        ("Laptops", 15, 9000), ("Smartphones", 5, 6000), ("LED TVs", 25, 8500),
        ("Headphones", 3, 2500), ("Tablets", 8, 5200), ("Smart Watches", 2, 3000),
        ("Printers", 20, 4000), ("Cameras", 6, 4800), ("Speakers", 12, 3500),
        ("Power Banks", 4, 2200), ("Keyboards", 7, 1800), ("Monitors", 18, 6500),
    ]
    return [Product(*d) for d in data]


def random_products(n: int, max_wt: int = 50, max_profit: int = 1000,
                    seed: int | None = None) -> list[Product]:
    rng = random.Random(seed)
    return [Product(f"Item{i + 1}", rng.randint(1, max_wt), rng.randint(10, max_profit))
            for i in range(n)]


def benchmark() -> list[tuple[int, int, float, float, float, float, float]]:
    """Measure running time and profit for different input sizes."""
    sizes = [10, 50, 100, 200, 500, 1000]
    rows = []
    print(f"\n{LINE}\n  PERFORMANCE BENCHMARK  (capacity = 10 x n, random data)\n{LINE}")
    print(f"  {'n':>6}{'Cap':>8}{'Frac ms':>11}{'Greedy01 ms':>13}{'DP ms':>11}"
          f"{'Greedy01/DP profit':>20}")
    print("  " + "-" * 69)
    for n in sizes:
        prods = random_products(n, seed=42)
        cap = n * 10
        f = fractional_knapsack(prods, cap)
        g = greedy_01_knapsack(prods, cap)
        d = dp_knapsack_01(prods, cap)
        acc = g.total_profit / d.total_profit * 100
        rows.append((n, cap, f.time_ms, g.time_ms, d.time_ms, g.total_profit, d.total_profit))
        print(f"  {n:>6}{cap:>8}{f.time_ms:>11.4f}{g.time_ms:>13.4f}{d.time_ms:>11.2f}"
              f"{acc:>19.2f}%")
    print("\n  Observation: Greedy stays almost instant (O(n log n)),")
    print("  while DP time grows quickly with n * W (O(n * W)).")
    return rows


def plot_benchmark() -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Please install matplotlib first:  pip install matplotlib")
        return
    rows = benchmark()
    ns = [r[0] for r in rows]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    ax[0].plot(ns, [r[2] for r in rows], "o-", label="Fractional Greedy")
    ax[0].plot(ns, [r[3] for r in rows], "s-", label="0/1 Greedy")
    ax[0].plot(ns, [r[4] for r in rows], "^-", label="DP 0/1")
    ax[0].set(xlabel="Number of products (n)", ylabel="Time (ms)",
              title="Execution Time", yscale="log")
    ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].plot(ns, [r[5] for r in rows], "s-", label="0/1 Greedy profit")
    ax[1].plot(ns, [r[6] for r in rows], "^-", label="DP 0/1 profit")
    ax[1].set(xlabel="Number of products (n)", ylabel="Total profit",
              title="Profit Comparison")
    ax[1].legend(); ax[1].grid(alpha=.3)
    plt.tight_layout()
    plt.savefig("benchmark.png", dpi=130)
    print("\nGraph saved: benchmark.png")


# ----------------------------------------------------------------------------
# 5. INTERACTIVE MENU
# ----------------------------------------------------------------------------
def read_int(prompt: str, minimum: int = 1) -> int:
    while True:
        try:
            v = int(input(prompt))
            if v >= minimum:
                return v
        except ValueError:
            pass
        print(f"  Please enter a whole number >= {minimum}.")


def input_products() -> list[Product]:
    n = read_int("How many products? ")
    items = []
    for i in range(1, n + 1):
        name = input(f"  Product {i} name: ").strip() or f"Item{i}"
        wt = read_int("    Weight (units): ")
        pr = read_int("    Profit (Rs.)  : ", minimum=0)
        items.append(Product(name, wt, pr))
    return items


def menu() -> None:
    products = sample_products()
    capacity = 60
    while True:
        print(f"\n{LINE}\n  INTELLIGENT INVENTORY MANAGER  (Knapsack Optimization)\n{LINE}")
        print("  1. View inventory")
        print("  2. Enter my own products")
        print("  3. Generate random products")
        print("  4. Set warehouse capacity")
        print("  5. Run Greedy (Fractional)")
        print("  6. Run DP (0/1)")
        print("  7. Compare all approaches")
        print("  8. Performance benchmark")
        print("  9. Exit")
        print(f"  [current: {len(products)} products, capacity {capacity}]")
        choice = input("\n  Choose (1-9): ").strip()

        if choice == "1":
            show_inventory(products, capacity)
        elif choice == "2":
            products = input_products()
        elif choice == "3":
            products = random_products(read_int("How many products? "))
        elif choice == "4":
            capacity = read_int("New capacity: ")
        elif choice == "5":
            show_result(fractional_knapsack(products, capacity), capacity)
        elif choice == "6":
            show_result(dp_knapsack_01(products, capacity), capacity)
        elif choice == "7":
            show_inventory(products, capacity)
            compare(products, capacity)
        elif choice == "8":
            benchmark()
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("  Invalid choice.")


def demo() -> None:
    products, capacity = sample_products(), 60
    show_inventory(products, capacity)
    compare(products, capacity)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "menu"
    {"demo": demo, "benchmark": benchmark, "plot": plot_benchmark}.get(mode, menu)()