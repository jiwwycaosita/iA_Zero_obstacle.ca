import unittest

from app.admissibility_core import evaluate_rules, operator_matches


class OperatorMatchesTest(unittest.TestCase):
    def test_numeric_comparisons(self):
        self.assertTrue(operator_matches(5, ">=", 5))
        self.assertFalse(operator_matches("5", ">=", 5))
        self.assertTrue(operator_matches(10, "<", 11))
        self.assertFalse(operator_matches(10, "<", 9))

    def test_membership_and_existence(self):
        self.assertTrue(operator_matches("qc", "in", ["qc", "on"]))
        self.assertFalse(operator_matches("ab", "in", ["qc", "on"]))
        self.assertTrue(operator_matches(None, "not_exists", None))
        self.assertFalse(operator_matches("value", "not_exists", None))

    def test_unknown_operator_fails(self):
        self.assertFalse(operator_matches(1, "unsupported", 1))


class AgentAdmissibilityTest(unittest.TestCase):
    def test_required_rules_gate_eligibility(self):
        profile = {"age": 30, "income": 20000}
        rules = [
            {
                "id": "age_min_18",
                "description": "Age minimum",
                "field": "age",
                "operator": ">=",
                "value": 18,
                "required": True,
            },
            {
                "id": "income_max_25000",
                "description": "Income ceiling",
                "field": "income",
                "operator": "<=",
                "value": 25000,
                "required": True,
            },
        ]

        result = evaluate_rules(profile, rules)
        self.assertTrue(result["eligible"])
        self.assertEqual(result["failed_rules"], [])

    def test_failed_required_rule_blocks_eligibility(self):
        profile = {"age": 30, "income": 50000}
        rules = [
            {
                "id": "income_max_25000",
                "description": "Income ceiling",
                "field": "income",
                "operator": "<=",
                "value": 25000,
                "required": True,
            }
        ]

        result = evaluate_rules(profile, rules)
        self.assertFalse(result["eligible"])
        self.assertEqual(result["failed_rules"], ["income_max_25000"])


if __name__ == "__main__":
    unittest.main()
