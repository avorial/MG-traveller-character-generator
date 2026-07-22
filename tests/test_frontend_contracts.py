"""Frontend/backend contract regressions."""

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
