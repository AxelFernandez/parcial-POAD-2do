import unittest

import numpy as np

from src.analysis import descriptive_summary, load_data, train_distance_model


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data()
        cls.model = train_distance_model(cls.data)

    def test_data_is_loaded_and_missing_targets_are_preserved(self):
        summary = descriptive_summary(self.data)

        self.assertEqual(summary["records"], 27143)
        self.assertEqual(summary["routes"], 107)
        self.assertEqual(summary["districts"], 24)
        self.assertEqual(summary["missing_distance"], 2415)
        self.assertEqual(len(self.data), 27143)

    def test_test_routes_do_not_appear_in_training(self):
        train_routes = set(self.model["train_routes"])
        test_routes = set(self.model["test_routes"])

        self.assertTrue(train_routes)
        self.assertTrue(test_routes)
        self.assertTrue(train_routes.isdisjoint(test_routes))

    def test_model_and_baseline_return_finite_metrics(self):
        self.assertGreater(self.model["target_rows"], 0)
        self.assertEqual(len(self.model["predictions"]), self.model["test_rows"])

        for method in ("baseline", "mlp"):
            self.assertTrue(np.isfinite(self.model[method]["mae"]))
            self.assertTrue(np.isfinite(self.model[method]["rmse"]))
            self.assertGreaterEqual(self.model[method]["mae"], 0)
            self.assertGreaterEqual(self.model[method]["rmse"], 0)


if __name__ == "__main__":
    unittest.main()
