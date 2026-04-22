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
app = FastAPI(title="Traveller Character Creator")

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


class CareerAction(CharacterAction):
    career_id: str
    assignment_id: str | None = None


class SkillTableAction(CharacterAction):
    table_key: str


class EndTermAction(CharacterAction):
    leaving: bool = False
    reason: str = "voluntary"


class MusterOutAction(CharacterAction):
    career_id: str
    column: str  # "cash" | "benefit"


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"species_list": list(rules.species().values()),
         "careers_list": list(rules.careers().values())},
    )


# ---------------------------------------------------------------------------
# Data endpoints (read-only lookups)
# ---------------------------------------------------------------------------

@app.get("/api/species")
async def api_species():
    return {"species": list(rules.species().values())}


@app.get("/api/careers")
async def api_careers():
    return {"careers": list(rules.careers().values())}


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


@app.post("/api/character/qualify")
async def api_qualify(action: CareerAction):
    character = action.character.model_copy(deep=True)
    try:
        return lifepath.qualify_for_career(character, action.career_id)
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


@app.post("/api/reload-rules")
async def api_reload_rules():
    """Dev helper — flush data caches without restarting."""
    rules.reload()
    return {"status": "rules reloaded"}


@app.get("/api/health")
async def api_health():
    return {"status": "ok", "species_count": len(rules.species()),
            "careers_count": len(rules.careers())}
