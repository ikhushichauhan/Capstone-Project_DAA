# StockKnap: Intelligent Inventory Management Using Knapsack Optimization

A full-stack web app that helps a warehouse manager choose which products to store so that
**total profit is maximised without exceeding the storage capacity**. It implements and compares:

| Approach | Problem solved | Time | Optimal? |
|---|---|---|---|
| Greedy, **Fractional Knapsack** | items may be split | O(n log n) | Yes (for fractional) |
| Greedy, whole items only *(bonus)* | 0/1, heuristic | O(n log n) | No |
| **Dynamic Programming, 0/1 Knapsack** | items taken whole or not at all | O(n·W) | Yes (for 0/1) |

## Quick start

```bash
cd inventory-knapsack
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. A new database is created automatically and filled with 10 sample
products (capacity 50 kg is a good demo: DP beats whole-item greedy).

## Project structure

```
inventory-knapsack/
├── app.py                  Flask app: REST API + page route
├── database.py             SQLite storage, validation, sample data
├── requirements.txt
├── algorithms/             <- the core of the project (no Flask code here)
│   ├── common.py           ratio, sorting, result builder
│   ├── greedy.py           fractional_knapsack(), greedy_whole_knapsack()
│   ├── dynamic.py          dp_knapsack(): table fill + backtracking
│   └── benchmark.py        random inventories + timing
├── templates/index.html    single-page UI (sidebar + 6 pages)
├── static/
│   ├── css/style.css
│   └── js/
│       ├── app.js          routing, API calls, rendering
│       └── charts.js       small SVG bar/line chart helpers (no libraries)
└── tests/
    ├── test_algorithms.py  correctness (incl. brute-force check of DP)
    └── test_api.py         API tests with a temporary database
```

## Pages in the app

1. **Inventory:** add, edit, delete, search and sort products (name, category, weight, profit).
2. **Optimize:** run one algorithm and see profit, space used, a capacity bar, the selected
   products, step-by-step decisions and, for DP, the full table with the backtrack path highlighted.
3. **Compare:** all three algorithms side by side: profit, utilisation, running time, two charts and a
   per-product decision matrix that highlights where greedy and DP disagree.
4. **Benchmark:** random inventories of growing size; chart and table of running times.
5. **History:** every comparison is saved to the database.
6. **Theory:** problem definition, pseudocode, complexity table and the classic "greedy fails" example.

The warehouse capacity (kg) is set once in the top bar and used everywhere.

## How the algorithms work

**Fractional greedy**: sort by `profit / weight` (descending); take whole items while they fit; take
the needed fraction of the first item that does not fit; stop.

**DP 0/1**: `dp[i][c]` = best profit using the first *i* items with capacity *c*.

```
dp[i][c] = dp[i-1][c]                                  if w_i > c
dp[i][c] = max(dp[i-1][c], dp[i-1][c - w_i] + p_i)     otherwise
```

The answer is `dp[n][W]`. Backtracking (`dp[i][c] != dp[i-1][c]` means item *i* was taken) gives the
chosen products. Weights and capacity must be **integers** because they index the table.

**Always true:** Fractional ≥ DP 0/1 ≥ Greedy (whole items).

## REST API

| Method | Endpoint | Purpose |
|---|---|---|
| GET / POST | `/api/products` | list / create |
| PUT / DELETE | `/api/products/<id>` | update / delete |
| DELETE | `/api/products` | delete all |
| POST | `/api/products/samples` | replace with sample data |
| POST | `/api/optimize` | `{capacity, algorithm: fractional \| greedy_whole \| dp}` |
| POST | `/api/compare` | `{capacity}`; runs all three and saves the run |
| POST | `/api/benchmark` | `{sizes: [..], repeats}` |
| GET / DELETE | `/api/history` | saved runs |

## Tests

```bash
python -m unittest discover -s tests -v
```

## Notes and limits

* Currency symbol and units: change `CURRENCY` at the top of `static/js/app.js` (default ₹, kg).
* DP table size is capped at 4 million cells to keep the server responsive; the table view in the UI
  is shown only for small problems (≤ 3,000 cells).
* Delete `inventory.db` to reset the app to the sample data.

## Ideas for extension

Item quantities (bounded knapsack), multiple warehouses, CSV import/export, user login.
