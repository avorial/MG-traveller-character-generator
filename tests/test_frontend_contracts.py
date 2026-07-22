"""Frontend/backend contract regressions."""

import ast
import pathlib
import re


ROOT = pathlib.Path(__file__).parent.parent


def test_life_event_choice_kinds_render_in_client():
    """Pending life-event kinds emitted by the engine must have JS UI branches."""
    engine = (ROOT / "app" / "engine" / "lifepath.py").read_text(encoding="utf-8")
    client = (ROOT / "app" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    emitted_kinds = set(re.findall(r'"kind": "([^"]+)"', engine))
    rendered_kinds = set(re.findall(r"kind === '([^']+)'", client))
    rendered_kinds.update(re.findall(r'kind === "([^"]+)"', client))

    # These are handled by non-life-event UI paths or are associate kinds inside data.
    ignored = {
        "ally",
        "contact",
        "enemy",
        "rival",
        "species_caste_choice",
        "species_skill_grant",
        "wife",
        "zhodani_psi_ruleset",
    }

    missing = sorted(emitted_kinds - rendered_kinds - ignored)
    assert missing == []


def test_dynamic_empty_pending_choices_are_populated_before_render():
    """Static pending choices with empty options must be filled dynamically."""
    engine = (ROOT / "app" / "engine" / "lifepath.py").read_text(encoding="utf-8")
    tree = ast.parse(engine)

    empty_pending_ids = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        items = {
            key.value: value
            for key, value in zip(node.keys, node.values)
            if isinstance(key, ast.Constant)
        }
        if (
            isinstance(items.get("type"), ast.Constant)
            and items["type"].value == "pending_choice"
            and isinstance(items.get("id"), ast.Constant)
            and isinstance(items.get("options"), ast.List)
            and not items["options"].elts
        ):
            empty_pending_ids.add(items["id"].value)

    dynamic_handlers = set(
        re.findall(r'choice_id == "([^"]+)":[\s\S]{0,900}?pending\["options"\] = opts', engine)
    )

    missing = sorted(empty_pending_ids - dynamic_handlers)
    assert missing == []


def test_character_load_paths_use_shared_transient_reset():
    """Import and save-slot loads should not retain stale per-character UI state."""
    client = (ROOT / "app" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert "function resetTransientUiStateForCharacterLoad()" in client
    assert client.count("resetTransientUiStateForCharacterLoad();") >= 3

    import_fn = client[client.index("async function importCharacter") :]
    import_fn = import_fn[: import_fn.index("// ============================================================")]
    assert "syncCapsuleFromCharacter();" not in import_fn
    assert "resetTransientUiStateForCharacterLoad();" in import_fn


def test_transient_ui_state_keys_are_reset_on_character_load():
    """All per-character uiState keys should be initialized and reset together."""
    client = (ROOT / "app" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    used = set(re.findall(r"uiState\.([A-Za-z_][A-Za-z0-9_]*)", client))
    init_block = client[
        client.index("let uiState = {") : client.index(
            "// ------------------------------------------------------------\n// Persistence"
        )
    ]
    reset_block = client[
        client.index("function resetTransientUiStateForCharacterLoad") : client.index(
            "function loadCharacter"
        )
    ]
    initialized = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*:", init_block))
    reset = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*:", reset_block))
    persistent_preferences = {
        "aiSettingsOpen",
        "gmMode",
        "hideDesc",
        "includeFoundrySource",
        "sheetTab",
        "theme",
    }

    assert sorted(used - initialized - persistent_preferences) == []
    assert sorted(used - reset - persistent_preferences) == []


def test_frontend_cascade_skills_include_backend_specialties():
    """Frontend specialty pickers must expose backend cascade skills."""
    client = (ROOT / "app" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    required_literals = [
        "'Animals':",
        "'Art':",
        "'Melee':          ['Blade', 'Bludgeon', 'Infighting', 'Natural', 'Unarmed']",
        "'Science':        ['Archaeology', 'Astronomy', 'Belief'",
    ]

    missing = [literal for literal in required_literals if literal not in client]
    assert missing == []
