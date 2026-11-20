# Intelligent Inventory Management Using Knapsack Optimization

A warehouse manager has limited storage capacity and many products, each with a
weight and a profit. This project selects products to **maximize total profit
without exceeding capacity**, and compares two approaches:

| Approach | Problem type | Time | Optimal? |
|---|---|---|---|
| Greedy (Fractional Knapsack) | Items can be split | O(n log n) | Yes (for fractional) |
| Dynamic Programming (0/1 Knapsack) | Items taken whole or not at all | O(n x W) | Yes (for 0/1) |

A third variant, greedy applied to whole items, is included to show where
greedy fails on the 0/1 problem.

## Files

| File | Purpose |
|---|---|
| `inventory.py` | Complete project: algorithms, interactive menu, demo and benchmark |

## Requirements

- Python 3.9 or newer
- No external libraries needed
- `matplotlib` is optional, only for the graph (`pip install matplotlib`)

## How to run

```bash
python inventory.py              # interactive menu
python inventory.py demo         # sample warehouse, all algorithms compared
python inventory.py benchmark    # timing table for n = 10 to 1000 products
python inventory.py plot         # saves benchmark.png (needs matplotlib)
```

## Input

From the menu you can:
- Enter your own products (name, weight, profit)
- Generate random products
- Set the warehouse capacity (default is 60)
- Or use the 12 built-in sample products

## Output

- The selected products and whether each was taken fully or partially
- Total profit, space used and running time
- A side-by-side comparison table of all three approaches
- A benchmark table (and optional graph) for different input sizes

## How it works

**Greedy (Fractional):** sort items by profit/weight ratio, take the best first,
and take a fraction of the last item if it does not fit.

**DP (0/1):** `dp[i][w]` is the maximum profit using the first `i` items with
capacity `w`. For each item, either skip it or take it, and keep the larger
value. The chosen items are recovered by backtracking through the table.

**Greedy (0/1):** the same ratio-based greedy, but only whole items are allowed.
It is fast, but it does not guarantee the optimal answer.

## Sample result (capacity 60, 12 products)

| Algorithm | Profit | Space used |
|---|---|---|
| Greedy (Fractional) | 38,838.89 | 60 / 60 |
| Greedy (0/1) | 36,200 | 55 / 60 |
| DP (0/1) | 37,000 | 57 / 60 |

Fractional greedy earns the most only because it splits a monitor, which a real
warehouse cannot do. For whole items, DP gives the best possible answer.

## Benchmark observation

Greedy stays almost instant even for 1000 products (about 0.3 ms), while DP
grows with n x W (about 1.6 seconds for n = 1000, capacity = 10000). Greedy is
faster, DP is guaranteed to be optimal for whole items.

## Conclusion

- Use **Fractional Greedy** when items can be divided (liquids, grains, bulk goods).
- Use **DP (0/1)** when items are indivisible (boxes, machines, devices).
- Use **0/1 Greedy** only when speed matters more than the best possible profit.
