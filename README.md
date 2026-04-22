# Traveller Character Creator

A web app for generating Mongoose Traveller characters through the full lifepath system — characteristics, species, background skills, careers (with survival rolls, events, mishaps, advancement), aging, and mustering out.

Built as a Docker-packaged FastAPI + Jinja2 + vanilla JS stack. All rules data (species, careers, tables) lives in editable JSON files, so adding a new race or completing a stubbed career is a matter of dropping a file in — no code changes required.

![Terminal aesthetic](https://img.shields.io/badge/aesthetic-1977%20CRT-orange) ![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Jinja-green) ![Docker](https://img.shields.io/badge/docker-compose%20up-blue)

## Running it

```bash
docker compose up
```

Then open <http://localhost:8000>. That's it.

The `app/` directory is mounted as a volume, so edits to JSON rule files, templates, CSS, or Python code hot-reload without a rebuild. Refresh the browser (or call `POST /api/reload-rules`) to pick up JSON changes.

Without Docker:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## What works

- **Full lifepath** — roll characteristics → pick species (modifiers + traits applied automatically) → background skills (gated by EDU DM) → career loop (qualify, assignment, skill training, survival, event, advancement) → mustering out with cash/benefits columns → aging rolls at term 4+.
- **Character state** lives in the browser (`localStorage`) and is sent to the stateless backend with each action. The server applies rules and returns the updated character plus a structured log entry.
- **Export/import** your Traveller as JSON from the footer.
- **Aging crisis detection** — any characteristic reduced to 0 by aging marks the character as dead; you can restart or manually revive via JSON edit.

### Careers

Four careers are **fully encoded** (qualification, assignments, full skill tables, events, mishaps, ranks, mustering-out benefits):

- **Agent** — Law Enforcement / Intelligence / Corporate
- **Army** — Support / Infantry / Cavalry
- **Noble** — Administrator / Diplomat / Dilettante
- **Scout** — Courier / Surveyor / Explorer

Eight careers are **stubbed** (qualification + assignments + survival/advancement only — events/mishaps/skill tables/mustering-out tables are empty):

Citizen, Drifter, Entertainer, Marine, Merchant, Navy, Rogue, Scholar.

You can play a stubbed career — you'll qualify, start a term, roll survival and advancement — but skill training and events return placeholder text until you fill the JSON in. See *Completing a career* below.

### Species

Three species are encoded: **Human**, **Aslan**, **Vargr**. Adding a new species is a single file in `app/data/species/`.

## Project structure

```
traveller-creator/
├── app/
│   ├── main.py                     # FastAPI routes
│   ├── engine/
│   │   ├── dice.py                 # 2D/1D/D3 rolling, characteristic DMs
│   │   ├── character.py            # Pydantic Character model (JSON-serializable)
│   │   ├── rules.py                # JSON data loader with lru_cache
│   │   └── lifepath.py             # The rules engine (qualify, survive, event, etc.)
│   ├── data/
│   │   ├── species/                # human.json, aslan.json, vargr.json — add more here
│   │   ├── careers/                # 12 career files
│   │   └── tables/                 # background_skills, life_events, injury, aging, mustering_benefits
│   ├── templates/
│   │   └── index.html              # Single Jinja2 template
│   └── static/
│       ├── css/style.css           # CRT terminal aesthetic
│       └── js/app.js               # Client-side phase controller (vanilla JS)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Extending it

### Adding a new species

Drop a file into `app/data/species/<id>.json`:

```json
{
  "id": "droyne",
  "name": "Droyne",
  "description": "An ancient, caste-based reptilian species of uncertain origin.",
  "characteristic_modifiers": {
    "STR": -2, "DEX": 0, "END": -1, "INT": 0, "EDU": 0, "SOC": 0
  },
  "characteristic_maximum": 15,
  "traits": [
    {
      "name": "Winged",
      "description": "Droyne can fly short distances in low-gravity environments."
    }
  ],
  "source": "Your source here"
}
```

Refresh the browser. The species appears in the species picker with its modifiers and traits.

### Completing a stubbed career

Look at `app/data/careers/scout.json` as the reference — it has every field filled in. For a stub like `app/data/careers/citizen.json`, you need to fill:

- `skill_tables` — 4+ tables (`personal_development`, `service_skills`, `advanced_education`, plus one per assignment), each keyed `1` through `6`
- `ranks` — either `default` (one rank track) or per-assignment, each with keys `0` through `6`, each entry `{"title": "...", "bonus": "..."}`
- `mishaps` — keyed `1` through `6`, values are text descriptions
- `events` — keyed `2` through `12`, values are text descriptions
- `mustering_out` — keyed `1` through `7`, each `{"cash": <credits>, "benefit": "<benefit name>"}`
- Set `"complete": true` when done

Source: Mongoose Traveller Core Rulebook pages 20–43.

### Adding a new career

Create `app/data/careers/<id>.json` using the full schema from Scout or Agent. It will appear in the career selector automatically.

## Notes on fidelity

This implementation covers the core lifepath faithfully but deliberately omits some edge cases for V1:

- **No pre-career education** (University, Military Academy) — can be added as a phase between background and career
- **No commissioning flow** — `commission` field is in Army/Marine/Navy data but the UI doesn't prompt for it yet
- **No draft** — failed qualification currently suggests "try another career" instead of rolling on the draft table
- **Event outcomes are not auto-applied** — the event text is displayed but any resulting skills/contacts/DMs must be applied manually to your notes (the engine does track `dm_next_advancement` / `dm_next_qualification` / `dm_next_benefit` for rules that set those)
- **No Connections Rule** — multi-player character linking is out of scope for single-player creation
- **Injury table** is defined but not auto-applied when a mishap says "roll on the Injury Table" — you can apply stat reductions manually via the exported JSON
- **Skill packages** at the end of creation are not modeled

The architecture supports adding all of these — the engine is structured so each rule is a function that takes a `Character` and returns the updated one.

## API

All endpoints accept `POST` with a `{"character": {...}, ...action_args}` body and return `{"character": {...}, ...result}`.

| Endpoint | Purpose |
| --- | --- |
| `/api/character/new` | Fresh empty character |
| `/api/character/roll-characteristics` | Roll 2D × 6 |
| `/api/character/apply-species` | Apply modifiers + traits |
| `/api/character/background-skills` | Grant background skills at level 0 |
| `/api/character/qualify` | Career qualification roll |
| `/api/character/start-term` | Begin a new term |
| `/api/character/survive` | Survival roll |
| `/api/character/event` | Event table (auto-handles Life Event sub-table) |
| `/api/character/mishap` | Mishap table |
| `/api/character/advance` | Advancement roll |
| `/api/character/skill-roll` | Roll on a specific skill table |
| `/api/character/end-term` | Close term (auto-handles aging at term 4+) |
| `/api/character/muster-out` | Cash or benefit roll from a career's mustering-out table |
| `/api/reload-rules` | Flush JSON caches without restart |
| `/api/health` | Sanity check |

## Legal

*Traveller* is a trademark of Far Future Enterprises, used under licence by Mongoose Publishing. The rules reproduced here are from the Mongoose Traveller Core Rulebook; this project is a fan tool for personal use at the table. Rules text in the JSON data files is paraphrased or quoted under fair use for game-aid purposes — please own the rulebook.
