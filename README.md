# Intelligent Inventory Management Using Knapsack Optimization

A warehouse manager has limited storage capacity and many products, each with a
weight and a profit. This project selects products to **maximize total profit
without exceeding capacity**, and compares two approaches:

| Approach | Problem type | Time | Optimal? |
|---|---|---|---|
| Greedy (Fractional Knapsack) | Items can be split | O(n log n) | Yes (for fractional) |
| Dynamic Programming (0/1 Knapsack) | Items taken whole or not at all | O(n x W) | Yes (for 0/1) |

A third, greedy-on-whole-items variant is included to show where greedy fails.

## Files

| File | Purpose |
|---|---|
| `inventory_knapsack.py` | Core algorithms + command-line menu, demo and benchmark |
| `app.py` | Web interface (Streamlit) |
| `requirements.txt` | Python dependencies |

## Setup

```bash
pip install -r requirements.txt
```

Python 3.9 or newer is required.

## Run

Command-line menu:

```bash
python inventory_knapsack.py
```

Other command-line modes:

```bash
python inventory_knapsack.py demo        # sample warehouse, all algorithms compared
python inventory_knapsack.py benchmark   # timing table for n = 10 to 1000
python inventory_knapsack.py plot        # saves benchmark.png
```

Web interface:

```bash
streamlit run app.py
```

It opens at http://localhost:8501.

## Hosting (free)

**Streamlit Community Cloud**
1. Push `app.py`, `inventory_knapsack.py` and `requirements.txt` to a public GitHub repo.
2. Go to https://share.streamlit.io, sign in with GitHub, click **New app**.
3. Select the repo, set the main file to `app.py`, and click **Deploy**.

You get a public link to share.

## How it works

**Greedy (Fractional):** sort items by profit/weight ratio, take the best first,
and take a fraction of the last item if it does not fit.

**DP (0/1):** `dp[i][w]` is the maximum profit using the first `i` items with
capacity `w`. For each item, either skip it or take it, and keep the larger
value. The chosen items are recovered by backtracking through the table.

## Sample result (capacity 60, 12 products)

| Algorithm | Profit |
|---|---|
| Greedy (Fractional) | 38,838.89 |
| Greedy (0/1) | 36,200 |
| DP (0/1) | 37,000 |

Fractional greedy earns the most only because it splits a monitor, which a real
warehouse cannot do. For whole items, DP gives the best possible answer.
