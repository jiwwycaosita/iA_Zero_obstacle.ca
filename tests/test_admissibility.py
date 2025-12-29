import pytest
from main import ProgramRule

def test_program_rule_creation():
    """Test création d'une règle d'admissibilité"""
    rule = ProgramRule(
        id="rule_1",
        description="Age minimum 18 ans",
        field="age",
        operator=">=",
        value=18,
        required=True
    )
    
    assert rule.id == "rule_1"
    assert rule.field == "age"
    assert rule.operator == ">="
    assert rule.value == 18
    assert rule.required == True

def test_admissibility_logic():
    """Test logique d'admissibilité basique"""
    user_profile = {"age": 25, "province": "QC"}
    
    # Simuler évaluation simple
    rule = ProgramRule(
        id="age_check",
        description="Age >= 18",
        field="age",
        operator=">=",
        value=18,
        required=True
    )
    
    # Test logique
    user_value = user_profile.get(rule.field)
    if rule.operator == ">=":
        result = user_value >= rule.value
    
    assert result == True
