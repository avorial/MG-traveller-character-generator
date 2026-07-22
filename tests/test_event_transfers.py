"""Career event transfer regressions."""

import ast
import pathlib

from app.engine import lifepath, rules
from app.engine.character import CareerTerm, Character


def test_lifepath_hardcoded_career_references_exist():
    """Literal career ids in lifepath effects must match real career ids."""
    valid_careers = set(rules.careers()) | {"any"}
    source = pathlib.Path(lifepath.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    refs = []

    class CareerRefVisitor(ast.NodeVisitor):
        tracked_attrs = {
            "pending_transfer_career_id",
            "forced_next_career_id",
            "auto_entry_career_id",
            "starts_commissioned_career_id",
            "academy_commission_career_id",
        }

        def visit_Assign(self, node):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and target.attr in self.tracked_attrs
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    refs.append((target.attr, node.value.value, node.lineno))
            self.generic_visit(node)

        def visit_Dict(self, node):
            items = {
                key.value: value
                for key, value in zip(node.keys, node.values)
                if isinstance(key, ast.Constant)
            }
            for field in ("career_id", "target_career_id"):
                value = items.get(field)
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    refs.append((field, value.value, node.lineno))
            value = items.get("career_ids")
            if isinstance(value, (ast.List, ast.Tuple)):
                for item in value.elts:
                    if isinstance(item, ast.Constant) and isinstance(item.value, str):
                        refs.append(("career_ids", item.value, node.lineno))
            self.generic_visit(node)

    CareerRefVisitor().visit(tree)
    invalid = [
        f"line {line}: {kind} -> {career_id!r}"
        for kind, career_id, line in refs
        if career_id not in valid_careers
    ]

    assert invalid == []


def test_navy_event_transfer_targets_marine_career_id():
    character = Character(phase="career")
    character.current_term = CareerTerm(
        career_id="navy",
        assignment_id="line_crew",
        term_number=1,
        overall_term_number=1,
        rank=0,
        survived=True,
    )
    character.pending_career_mishap_choice = {
        "type": "pending_choice",
        "id": "event_navy_transfer",
        "prompt": "Transfer to Marines?",
        "options": [{"id": "transfer", "label": "Transfer"}],
    }

    lifepath.resolve_career_mishap_choice(character, {"option_id": "transfer"})

    assert character.pending_transfer_career_id == "marine"


def test_ladybug_marine_qualification_penalty_applies():
    character = Character(phase="career", species_id="ladybug")
    character.characteristics.END = 8

    from app.engine import dice

    dice.set_forced_rolls([7])
    try:
        result = lifepath.qualify_for_career(character, "marine")
    finally:
        dice.clear_forced_rolls()

    assert result["roll"]["modifier"] == -2
    assert result["roll"]["total"] == 5
    assert result["succeeded"] is False


def test_species_allowed_career_ids_blocks_disallowed_careers():
    character = Character(phase="career", species_id="gmina")

    result = lifepath.qualify_for_career(character, "army")

    assert result["succeeded"] is False
    assert result["reason"] == "Gmina may only enter: Drifter."
