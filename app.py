"""Flask application: REST API + single-page UI for the inventory optimizer."""
from flask import Flask, jsonify, render_template, request

import database as db
from algorithms import (
    dp_knapsack,
    fractional_knapsack,
    greedy_whole_knapsack,
    run_benchmark,
)
from algorithms.benchmark import MAX_ITEMS

app = Flask(__name__)
db.init_db()

MAX_CAPACITY = 100_000


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


@app.errorhandler(ApiError)
def handle_api_error(err):
    return jsonify(error=err.message), err.status


@app.errorhandler(ValueError)
def handle_value_error(err):
    return jsonify(error=str(err)), 400


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def read_json():
    return request.get_json(silent=True) or {}


def parse_capacity(payload):
    try:
        value = float(payload.get("capacity"))
    except (TypeError, ValueError):
        raise ApiError("Capacity must be a number.")
    if not value.is_integer() or value <= 0:
        raise ApiError("Capacity must be a positive whole number of kg.")
    if value > MAX_CAPACITY:
        raise ApiError(f"Capacity must not exceed {MAX_CAPACITY:,} kg.")
    return int(value)


def require_items():
    items = db.list_products()
    if not items:
        raise ApiError("Your inventory is empty. Add products first.")
    return items


def averaged(fn, repeats):
    """Run an algorithm several times and report the average running time."""
    total, result = 0.0, None
    for _ in range(repeats):
        result = fn()
        total += result["time_ms"]
    result["time_ms"] = round(total / repeats, 4)
    return result


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html")


# --------------------------------------------------------------------------
# Products API
# --------------------------------------------------------------------------
@app.get("/api/products")
def products_list():
    return jsonify(db.list_products())


@app.post("/api/products")
def products_create():
    return jsonify(db.add_product(read_json())), 201


@app.put("/api/products/<int:pid>")
def products_update(pid):
    product = db.update_product(pid, read_json())
    if product is None:
        raise ApiError("Product not found.", 404)
    return jsonify(product)


@app.delete("/api/products/<int:pid>")
def products_delete(pid):
    if not db.delete_product(pid):
        raise ApiError("Product not found.", 404)
    return jsonify(ok=True)


@app.delete("/api/products")
def products_clear():
    db.clear_products()
    return jsonify(ok=True)


@app.post("/api/products/samples")
def products_samples():
    db.load_samples()
    return jsonify(db.list_products())


# --------------------------------------------------------------------------
# Optimisation API
# --------------------------------------------------------------------------
@app.post("/api/optimize")
def optimize():
    payload = read_json()
    capacity = parse_capacity(payload)
    key = payload.get("algorithm", "dp")
    items = require_items()

    if key == "fractional":
        result = fractional_knapsack(items, capacity)
    elif key == "greedy_whole":
        result = greedy_whole_knapsack(items, capacity)
    elif key == "dp":
        result = dp_knapsack(items, capacity, return_table=True)
    else:
        raise ApiError("Unknown algorithm.")
    return jsonify(result)


@app.post("/api/compare")
def compare():
    payload = read_json()
    capacity = parse_capacity(payload)
    items = require_items()

    n = len(items)
    dp_repeats = 5 if n * capacity <= 200_000 else 1

    results = {
        "fractional": averaged(
            lambda: fractional_knapsack(items, capacity, trace=False), 20),
        "greedy_whole": averaged(
            lambda: greedy_whole_knapsack(items, capacity, trace=False), 20),
        "dp": averaged(
            lambda: dp_knapsack(items, capacity, trace=False), dp_repeats),
    }

    frac, whole, dp = results["fractional"], results["greedy_whole"], results["dp"]
    summary = {
        "dp_minus_greedy_whole": round(dp["total_profit"] - whole["total_profit"], 2),
        "gap_percent": round(
            100 * (dp["total_profit"] - whole["total_profit"]) / dp["total_profit"], 2
        ) if dp["total_profit"] else 0.0,
        "fractional_minus_dp": round(frac["total_profit"] - dp["total_profit"], 2),
        "dp_slowdown": round(dp["time_ms"] / max(frac["time_ms"], 1e-6), 1),
    }

    db.save_run(capacity, n, results)

    return jsonify({
        "capacity": capacity,
        "n_items": n,
        "total_stock_weight": sum(i["weight"] for i in items),
        "items": items,
        "results": results,
        "summary": summary,
    })


@app.post("/api/benchmark")
def benchmark():
    payload = read_json()
    sizes = payload.get("sizes", [10, 25, 50, 100, 200])
    repeats = payload.get("repeats", 3)

    if (not isinstance(sizes, list) or not 1 <= len(sizes) <= 10
            or not all(isinstance(s, int) and 1 <= s <= MAX_ITEMS for s in sizes)):
        raise ApiError(f"Sizes must be 1-10 whole numbers between 1 and {MAX_ITEMS}.")
    if not isinstance(repeats, int) or not 1 <= repeats <= 10:
        raise ApiError("Repeats must be between 1 and 10.")

    return jsonify({"rows": run_benchmark(sorted(set(sizes)), repeats)})


# --------------------------------------------------------------------------
# History API
# --------------------------------------------------------------------------
@app.get("/api/history")
def history_list():
    return jsonify(db.list_runs())


@app.delete("/api/history")
def history_clear():
    db.clear_runs()
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
