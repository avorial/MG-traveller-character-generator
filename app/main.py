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

from .engine import lifepath, rules, dice as _dice
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


@app.middleware("http")
async def clear_gm_rolls_after_request(request: Request, call_next):
    response = await call_next(request)
    _dice.clear_forced_rolls()
    return response


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CharacterAction(BaseModel):
    """Base shape for any action — character state plus optional action params."""
    character: Character
    # GM Mode: list of raw dice totals to use instead of rolling randomly,
    # consumed in sequence. Ignored when empty.
    gm_rolls: list[int] = []

    def model_post_init(self, __context) -> None:
        if self.gm_rolls:
            _dice.set_forced_rolls(self.gm_rolls)


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


class EventTransferOfferAction(CharacterAction):
    """Accept an event's career-transfer offer (e.g. army[10] 'transfer to
    the Marines without a Qualification roll'). Stores a pending transfer
    that the next qualify call consumes."""
    target_career_id: str


class EventStatChangeAction(CharacterAction):
    """Apply a ±N delta to a characteristic from an event branch (e.g.
    noble[3] refuse: SOC -1; noble[3] accept+success: SOC +1)."""
    stat: str
    delta: int
    reason: str = ""


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
    use_good_fortune: bool = False


class PreCareerQualifyAction(CharacterAction):
    track: str  # "university" | "military_academy" | "merchant_academy" | etc.
    service: str | None = None    # "army" | "marine" | "navy" (military_academy only)
    curriculum: str | None = None  # "business" | "shipboard" (merchant_academy only)


class PreCareerGraduateAction(CharacterAction):
    chosen_skills: list[str] = []


class PreCareerSkillsAction(CharacterAction):
    chosen_skills: list[str]


class PreCareerEvent10Action(CharacterAction):
    skill_text: str


class PreCareerEvent11Action(CharacterAction):
    choice: str  # "drifter" | "draft" | "dodge"


class LifeEventChoiceAction(CharacterAction):
    choice: str  # "rival" | "enemy" | "lose_benefit" | "prisoner"


class InjuryChoiceAction(CharacterAction):
    chosen_stat: str  # "STR" | "DEX" | "END"


class CareerMishapChoiceAction(CharacterAction):
    choice_data: dict = {}


class CrossCareerRollAction(CharacterAction):
    career_id: str
    table: str  # "event" | "mishap"


class BanCareerAction(CharacterAction):
    career_id: str


class SkillPackageAction(CharacterAction):
    package_id: str


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
         "skills_data": rules.skills(),
         "societies_list": rules.list_societies(),
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


@app.get("/api/careers/full")
async def api_careers_full():
    """Full career data including tables (service_skills, advanced_education,
    officer, etc.) — used by the event-wildcard skill picker on the client."""
    return {"careers": rules.careers()}


@app.get("/api/background-skills")
async def api_background_skills():
    return rules.background_skills()


@app.get("/api/skill-packages")
async def api_skill_packages():
    return rules.skill_packages()


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


@app.post("/api/character/racial-background-roll")
async def api_racial_background_roll(action: CharacterAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.racial_background_roll(character)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/background-skills")
async def api_background_skills_set(action: BackgroundSkillsAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.set_background_skills(character, action.chosen)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/apply-skill-package")
async def api_apply_skill_package(action: SkillPackageAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.apply_skill_package(character, action.package_id)
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
        return lifepath.pre_career_qualify(
            character, action.track, action.service, action.curriculum
        )
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


@app.post("/api/character/pre-career/any-skill")
async def api_pre_career_any_skill(action: EventSkillGrantAction):
    """Grant the free 'any skill at level 0' from education event 9."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.pre_career_grant_any_skill(character, action.skill_text)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/pre-career/event10-skill")
async def api_pre_career_event10_skill(action: PreCareerEvent10Action):
    """Education event 10 — tutor challenge: pick a skill and roll 2D 9+."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.pre_career_event10_skill(character, action.skill_text)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/pre-career/event11-choice")
async def api_pre_career_event11_choice(action: PreCareerEvent11Action):
    """Education event 11 — draft event: choose Drifter, Draft, or Dodge."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.pre_career_event11_choice(character, action.choice)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/life-event")
async def api_life_event(action: CharacterAction):
    """Roll 2D on the Life Events table and auto-apply the result."""
    character = action.character.model_copy(deep=True)
    try:
        result = lifepath.apply_life_event(character)
        result["character"] = character.model_dump()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/life-event-choice")
async def api_life_event_choice(action: LifeEventChoiceAction):
    """Resolve a pending interactive Life Event choice."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.resolve_life_event_choice(character, action.choice)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/injury-choice")
async def api_injury_choice(action: InjuryChoiceAction):
    """Resolve a pending injury stat choice (which characteristic absorbs damage)."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.resolve_injury_choice(character, action.chosen_stat)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/pre-career/event")
async def api_pre_career_event(action: CharacterAction):
    """Roll one event on the pre-career events table (2D). Called once per year
    of the track; graduation is only available after all events are rolled."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.pre_career_event_roll(character)
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


@app.post("/api/character/career-mishap-choice")
async def api_career_mishap_choice(action: CareerMishapChoiceAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.resolve_career_mishap_choice(character, action.choice_data)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/cross-career-roll")
async def api_cross_career_roll(action: CrossCareerRollAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.cross_career_event_or_mishap(character, action.career_id, action.table)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/ban-career")
async def api_ban_career(action: BanCareerAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.ban_career(character, action.career_id)
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


@app.post("/api/character/event-transfer-offer")
async def api_event_transfer_offer(action: EventTransferOfferAction):
    """Accept a career-transfer offer from an event (skips next qualify)."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.accept_transfer_offer(character, action.target_career_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/character/event-stat-change")
async def api_event_stat_change(action: EventStatChangeAction):
    """Apply a characteristic delta from an event branch (noble duel, etc.)."""
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.apply_event_stat_change(
            character, action.stat, action.delta, action.reason
        )
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
        return lifepath.muster_out_roll(
            character, action.career_id, action.column, action.use_good_fortune
        )
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


@app.get("/api/tables/skills")
async def api_skills():
    return rules.skills()


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


@app.get("/api/character/generate-npc")
async def api_generate_npc():
    """Generate a fully fleshed-out NPC character server-side."""
    try:
        return lifepath.generate_npc()
    except Exception as e:
        raise HTTPException(500, str(e))
