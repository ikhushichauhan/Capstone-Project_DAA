"""API tests using Flask's test client and a throw-away database."""
import os
import sys
import tempfile
import unittest

# The DB path must be set BEFORE the app is imported.
_tmp = tempfile.mkdtemp()
os.environ["KNAPSACK_DB"] = os.path.join(_tmp, "test.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.post("/api/products/samples")

    def test_index_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"StockKnap", res.data)

    def test_product_crud(self):
        res = self.client.post("/api/products", json={
            "name": "Test Box", "category": "Test", "weight": 7, "profit": 99.5})
        self.assertEqual(res.status_code, 201)
        pid = res.get_json()["id"]

        res = self.client.put(f"/api/products/{pid}", json={
            "name": "Test Box 2", "category": "Test", "weight": 8, "profit": 120})
        self.assertEqual(res.get_json()["weight"], 8)

        self.assertEqual(self.client.delete(f"/api/products/{pid}").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/products/{pid}").status_code, 404)

    def test_validation(self):
        bad = [
            {"name": "", "weight": 5, "profit": 10},
            {"name": "x", "weight": 2.5, "profit": 10},
            {"name": "x", "weight": -1, "profit": 10},
            {"name": "x", "weight": 5, "profit": 0},
            {"name": "x", "weight": "abc", "profit": 10},
        ]
        for payload in bad:
            res = self.client.post("/api/products", json=payload)
            self.assertEqual(res.status_code, 400, payload)
            self.assertIn("error", res.get_json())

    def test_optimize_each_algorithm(self):
        profits = {}
        for key in ("fractional", "greedy_whole", "dp"):
            res = self.client.post("/api/optimize", json={"capacity": 50, "algorithm": key})
            self.assertEqual(res.status_code, 200)
            profits[key] = res.get_json()["total_profit"]
        self.assertGreaterEqual(profits["fractional"], profits["dp"])
        self.assertGreater(profits["dp"], profits["greedy_whole"])   # sample-data demo

    def test_optimize_errors(self):
        self.assertEqual(
            self.client.post("/api/optimize", json={"capacity": 0}).status_code, 400)
        self.assertEqual(
            self.client.post("/api/optimize", json={"capacity": 50, "algorithm": "x"}).status_code, 400)
        self.client.delete("/api/products")
        self.assertEqual(
            self.client.post("/api/optimize", json={"capacity": 50}).status_code, 400)

    def test_compare_saves_history(self):
        self.client.delete("/api/history")
        res = self.client.post("/api/compare", json={"capacity": 50})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(set(data["results"]), {"fractional", "greedy_whole", "dp"})
        self.assertEqual(len(self.client.get("/api/history").get_json()), 1)

    def test_benchmark(self):
        res = self.client.post("/api/benchmark", json={"sizes": [10, 20], "repeats": 1})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()["rows"]), 2)
        res = self.client.post("/api/benchmark", json={"sizes": [99999]})
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
