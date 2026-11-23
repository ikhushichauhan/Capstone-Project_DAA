"""Unit tests for the knapsack algorithms.  Run:  python -m unittest discover -s tests -v"""
import itertools
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms import (  # noqa: E402
    dp_knapsack,
    fractional_knapsack,
    generate_items,
    greedy_whole_knapsack,
)


def make_items(pairs):
    return [{"id": i + 1, "name": f"I{i + 1}", "weight": w, "profit": p}
            for i, (w, p) in enumerate(pairs)]


def brute_force(items, capacity):
    best = 0
    for r in range(len(items) + 1):
        for combo in itertools.combinations(items, r):
            if sum(i["weight"] for i in combo) <= capacity:
                best = max(best, sum(i["profit"] for i in combo))
    return best


# Classic textbook example: weights 10/20/30, profits 60/100/120, capacity 50
CLASSIC = make_items([(10, 60), (20, 100), (30, 120)])


class ClassicExample(unittest.TestCase):
    def test_fractional(self):
        res = fractional_knapsack(CLASSIC, 50)
        self.assertEqual(res["total_profit"], 240)
        self.assertEqual(res["total_weight"], 50)
        fractions = {s["id"]: s["fraction"] for s in res["selected"]}
        self.assertEqual(fractions, {1: 1.0, 2: 1.0, 3: round(20 / 30, 4)})

    def test_dp(self):
        res = dp_knapsack(CLASSIC, 50)
        self.assertEqual(res["total_profit"], 220)
        self.assertEqual({s["id"] for s in res["selected"]}, {2, 3})

    def test_greedy_whole_is_not_optimal(self):
        res = greedy_whole_knapsack(CLASSIC, 50)
        self.assertEqual(res["total_profit"], 160)   # DP finds 220
        self.assertLess(res["total_profit"], dp_knapsack(CLASSIC, 50)["total_profit"])


class Properties(unittest.TestCase):
    def test_dp_matches_brute_force(self):
        rng = random.Random(1)
        for _ in range(60):
            items = make_items([(rng.randint(1, 12), rng.randint(1, 60))
                                for _ in range(rng.randint(1, 9))])
            cap = rng.randint(1, 40)
            self.assertEqual(dp_knapsack(items, cap)["total_profit"],
                             brute_force(items, cap))

    def test_ordering_fractional_ge_dp_ge_greedy_whole(self):
        for n in (5, 20, 60):
            items = generate_items(n)
            cap = sum(i["weight"] for i in items) // 2
            frac = fractional_knapsack(items, cap)["total_profit"]
            dp = dp_knapsack(items, cap)["total_profit"]
            whole = greedy_whole_knapsack(items, cap)["total_profit"]
            self.assertGreaterEqual(frac + 1e-9, dp)
            self.assertGreaterEqual(dp, whole)

    def test_capacity_never_exceeded(self):
        items = generate_items(40)
        for cap in (1, 17, 100, 5000):
            for fn in (fractional_knapsack, greedy_whole_knapsack, dp_knapsack):
                self.assertLessEqual(fn(items, cap)["total_weight"], cap + 1e-9)

    def test_dp_backtrack_profit_matches_table(self):
        items = generate_items(15)
        res = dp_knapsack(items, 60, return_table=True)
        self.assertEqual(res["total_profit"], res["table"]["rows"][-1][-1])

    def test_everything_fits(self):
        items = make_items([(2, 10), (3, 20)])
        for fn in (fractional_knapsack, greedy_whole_knapsack, dp_knapsack):
            self.assertEqual(fn(items, 100)["total_profit"], 30)

    def test_nothing_fits(self):
        items = make_items([(10, 50), (20, 90)])
        self.assertEqual(dp_knapsack(items, 5)["total_profit"], 0)
        self.assertEqual(greedy_whole_knapsack(items, 5)["total_profit"], 0)
        self.assertGreater(fractional_knapsack(items, 5)["total_profit"], 0)

    def test_dp_size_guard(self):
        items = generate_items(500)
        with self.assertRaises(ValueError):
            dp_knapsack(items, 90_000)


if __name__ == "__main__":
    unittest.main()
