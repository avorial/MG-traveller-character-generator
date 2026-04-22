"""
FastAPI entrypoint for the Traveller character creator.

The backend is deliberately stateless — the character lives in the browser
(localStorage) and is sent along with each request. The server applies rules
and returns the updated character plus a structured log of what happened.
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .engine import lifepath, rules
from .engine.character import Character, new_character


BASE_DIR = Path(__file__).parent

# VERSION lives at the repo root alongside docker-compose.yml and is
# bumped by push-to-github.ps1 on every release. We read it once at
# startup and surface it in the UI (and via /api/health).
_VERSION_FILE = BASE_DIR.parent / "VERSION"
try:
    APP_VERSION = _VERSION_FILE.read_text(encoding="utf-8").strip() or "dev"
except FileNotFoundError:
    APP_VERSION = "dev"

app = FastAPI(title="Traveller Character Creator", version=APP_VERSION)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CharacterAction(BaseModel):
    """Base shape for any action — character state plus optional action params."""
    character: Character


class SpeciesAction(CharacterAction):
    species_id: str


class BackgroundSkillsAction(CharacterAction):
    chosen: list[str]


class SwapStatsAction(CharacterAction):
    stat_a: str
    stat_b: str


class BoonAction(CharacterAction):
    stat: str


class BoonPoolAction(CharacterAction):
    count: int


class ConnectionAction(CharacterAction):
    description: str
    skill: str | None = None


class PsionicTalentAction(CharacterAction):
    talent_id: str





class CareerAction(CharacterAction):
    career_id: str
    assignment_id: str | None = None


class SkillTableAction(CharacterAction):
    table_key: str


class EventSkillGrantAction(CharacterAction):
    skill_text: str


class EventDmGrantAction(CharacterAction):
    dm: int
    target: str


class AssociateAction(CharacterAction):
    """Add a new Associate or convert an existing Contact/Ally → Rival/Enemy."""
    op: str  # "add" | "convert"
    kind: str | None = None         # required for op="add"  — "contact"|"ally"|"rival"|"enemy"
    description: str | None = None  # optional for op="add"
    index: int | None = None        # required for op="convert" — index into character.associates
    to_kind: str | None = None      # required for op="convert" — "rival"|"enemy"


class EndTermAction(CharacterAction):
    leaving: bool = False
    reason: str = "voluntary"


class MusterOutAction(CharacterAction):
    career_id: str
    column: str  # "cash" | "benefit"


class PreCareerQualifyAction(CharacterAction):
    track: str  # "university" | "military_academy"
    service: str | None = None  # "army" | "marine" | "navy" (academy only)


class PreCareerGraduateAction(CharacterAction):
    chosen_skills: list[str] = []


class PreCareerSkillsAction(CharacterAction):
    chosen_skills: list[str]


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"species_list": rules.list_species(),
         "careers_list": rules.list_careers(),
         "app_version": APP_VERSION},
    )


# ---------------------------------------------------------------------------
# Data endpoints (read-only lookups)
# ---------------------------------------------------------------------------

@app.get("/api/species")
async def api_species():
    return {"species": rules.list_species()}


@app.get("/api/careers")
async def api_careers():
    return {"careers": rules.list_careers()}


@app.get("/api/background-skills")
async def api_background_skills():
    return rules.background_skills()


@app.get("/api/tables/aging")
async def api_aging():
    return rules.aging_table()


@app.get("/api/tables/injury")
async def api_injury():
    return rules.injury_table()


@app.get("/api/tables/life-events")
async def api_life_events():
    return rules.life_events()


@app.get("/api/tables/mustering-benefits")
async def api_mustering_benefits():
    return rules.mustering_benefits()


@app.get("/api/tables/education")
async def api_education():
    return rules.education()


# ---------------------------------------------------------------------------
# Character actions
# ---------------------------------------------------------------------------

@app.post("/api/character/new")
async def api_new_character():
    return {"character": new_character().model_dump()}


@app.post("/api/character/roll-characteristics")
async def api_roll_characteristics(action: CharacterAction):
    character = action.character.model_copy(deep=True)
    result = lifepath.roll_initial_characteristics(character)
    return result


@app.post("/api/character/swap-stats")
async def api_swap_stats(action: SwapStatsAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.swap_characteristics(character, action.stat_a, action.stat_b)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/apply-species")
async def api_apply_species(action: SpeciesAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.apply_species(character, action.species_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/background-skills")
async def api_background_skills_set(action: BackgroundSkillsAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.set_background_skills(character, action.chosen)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/pre-career/skip")
async def api_pre_career_skip(action: CharacterAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.skip_pre_career(character)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/pre-career/qualify")
async def api_pre_career_qualify(action: PreCareerQualifyAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.pre_career_qualify(character, action.track, action.service)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/pre-career/graduate")
async def api_pre_career_graduate(action: PreCareerGraduateAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.pre_career_graduate(character, action.chosen_skills or None)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/pre-career/choose-skills")
async def api_pre_career_choose_skills(action: PreCareerSkillsAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.pre_career_choose_skills(character, action.chosen_skills)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/qualify")
async def api_qualify(action: CareerAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.qualify_for_career(character, action.career_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/draft")
async def api_draft(action: CharacterAction):
    """Roll 1d6 on the draft table and auto-start the drafted term.

    Called after a failed career qualification when the player elects to
    accept the draft instead of falling back to Drifter.
    """
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.draft_into_service(character)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/start-term")
async def api_start_term(action: CareerAction):
    if not action.assignment_id:
        raise HTTPException(400, "assignment_id is required")
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.start_term(character, action.career_id, action.assignment_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/survive")
async def api_survive(action: CharacterAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.survival_roll(character)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/event")
async def api_event(action: CharacterAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.event_roll(character)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/mishap")
async def api_mishap(action: CharacterAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.mishap_roll(character)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/advance")
async def api_advance(action: CharacterAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.advancement_roll(character)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/skill-roll")
async def api_skill_roll(action: SkillTableAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.roll_on_skill_table(character, action.table_key)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/event-skill-grant")
async def api_event_skill_grant(action: EventSkillGrantAction):
    """Apply a skill chosen from an event that offered multiple options."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.grant_event_skill(character, action.skill_text)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/event-dm-grant")
async def api_event_dm_grant(action: EventDmGrantAction):
    """Apply the 'DM+N' side of an 'either skill or DM+N' event choice."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.grant_event_dm(character, action.dm, action.target)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/associate")
async def api_associate(action: AssociateAction):
    """Mutate the Associates list: add a new one, or convert Contact/Ally → Rival/Enemy."""
    character = action.character.model_copy(deep=True)
    try:
        if action.op == "add":
            return lifepath.add_associate(
                character, action.kind or "", action.description or ""
            )
        if action.op == "convert":
            return lifepath.convert_associate(
                character, action.index if action.index is not None else -1, action.to_kind or ""
            )
        raise HTTPException(400, f"Unknown associate op: {action.op!r}")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/end-term")
async def api_end_term(action: EndTermAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.end_term(character, leaving=action.leaving, reason=action.reason)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/muster-out")
async def api_muster_out(action: MusterOutAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.muster_out_roll(character, action.career_id, action.column)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/anagathics")
async def api_anagathics(action: CharacterAction):
    """Purchase one term of anagathics treatment."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.purchase_anagathics(character)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/injury")
async def api_character_injury(action: CharacterAction):
    """Roll on the injury table (1D). Applies stat damage + medical debt."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.apply_injury(character)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/boon")
async def api_boon(action: BoonAction):
    """Re-roll one characteristic, keeping the higher value (boon)."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.reroll_characteristic_boon(character, action.stat)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/boon-pool")
async def api_boon_pool(action: BoonPoolAction):
    """Set the boon-roll pool size (GM-configurable)."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.set_boon_pool(character, action.count)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/capsule")
async def api_capsule(action: CharacterAction):
    """Generate a capsule description of the character."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.generate_capsule(character)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/connection")
async def api_connection(action: ConnectionAction):
    """Add a Connection (a link to another PC) to the character."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.add_connection(character, action.description, action.skill)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/tables/psionics")
async def api_psionics_table():
    return rules.psionics()


@app.post("/api/character/psionics/test")
async def api_psionics_test(action: CharacterAction):
    """Run the psionic potential test (2D 9+) and roll Psi on success."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.test_psionics(character)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/psionics/train")
async def api_psionics_train(action: PsionicTalentAction):
    """Train a specific psionic talent (costs Cr per talent)."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.train_psionic_talent(character, action.talent_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/reload-rules")
async def api_reload_rules():
    """Dev helper - flush data caches without restarting."""
    rules.reload()
    return {"status": "rules reloaded"}


@app.get("/api/health")
async def api_health():
    """Simple liveness check."""
    return {"status": "ok", "version": APP_VERSION}
