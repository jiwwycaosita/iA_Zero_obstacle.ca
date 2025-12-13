"""Noyau déterministe pour l'évaluation d'admissibilité sans dépendance FastAPI.

Ce module est volontairement léger pour pouvoir être testé sans installer
l'ensemble des dépendances serveur. Il expose les opérateurs supportés ainsi
qu'une fonction utilitaire d'évaluation utilisée par l'agent.
"""
from typing import Any, Callable, Dict, List, Mapping


RuleMapping = Mapping[str, Any]


def get_profile_value(profile: Mapping[str, Any], field_path: str) -> Any:
    current: Any = profile
    for part in field_path.split("."):
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            return None
    return current


def operator_matches(value: Any, operator: str, expected: Any) -> bool:
    ops: Dict[str, Callable[[Any, Any], bool]] = {
        "==": lambda a, b: a == b,
        "=": lambda a, b: a == b,
        "eq": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        "neq": lambda a, b: a != b,
        ">": lambda a, b: isinstance(a, (int, float)) and a > b,
        ">=": lambda a, b: isinstance(a, (int, float)) and a >= b,
        "<": lambda a, b: isinstance(a, (int, float)) and a < b,
        "<=": lambda a, b: isinstance(a, (int, float)) and a <= b,
        "in": lambda a, b: a in b if isinstance(b, (list, tuple, set)) else False,
        "not_in": lambda a, b: a not in b if isinstance(b, (list, tuple, set)) else False,
        "exists": lambda a, _: a is not None,
        "not_exists": lambda a, _: a is None,
    }

    matcher = ops.get(operator.lower()) if isinstance(operator, str) else None
    if not matcher:
        return False
    try:
        return matcher(value, expected)
    except Exception:
        return False


def evaluate_rules(user_profile: Mapping[str, Any], program_rules: List[RuleMapping]) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    failed_rules: List[str] = []

    for rule in program_rules:
        field = rule.get("field", "")
        operator = rule.get("operator", "")
        value = rule.get("value")
        required = bool(rule.get("required", True))
        rule_id = rule.get("id", "")

        profile_value = get_profile_value(user_profile, field)
        passed = operator_matches(profile_value, operator, value)
        if not passed and required:
            failed_rules.append(rule_id)

        results.append(
            {
                "id": rule_id,
                "field": field,
                "operator": operator,
                "expected": value,
                "value": profile_value,
                "required": required,
                "passed": passed,
            }
        )

    eligible = len([r for r in program_rules if r.get("required", True)]) == 0 or len(failed_rules) == 0

    return {
        "eligible": eligible,
        "failed_rules": failed_rules,
        "details": "Calcul local sans LLM; les règles non satisfaites sont listées.",
        "rule_results": results,
    }
