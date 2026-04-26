# Traveller Character Creator

A web app for generating Mongoose Traveller 2e characters through the complete lifepath system — characteristics, species, pre-career education, careers (qualify, survive, events, mishaps, advancement, aging), mustering out, psionics, and a final character sheet with capsule description.

Built as a Docker-packaged FastAPI + Jinja2 + vanilla JS stack. All rules data lives in editable JSON files — no code changes required to add a new career, species, or tweak a table.

![Version](https://img.shields.io/badge/version-5.1-blue) ![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Jinja-green) ![Docker](https://img.shields.io/badge/docker-compose%20up-blue)

---

## Running it

```bash
docker compose up
```

Open <http://localhost:8000>. That's it.

The `app/` directory is mounted as a volume — edits to JSON rule files, templates, CSS, or Python hot-reload without a rebuild. Refresh the browser (or `POST /api/reload-rules`) to pick up JSON changes.

Without Docker:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## What's implemented

### Full lifepath phases

1. **Characteristics** — Roll 2D×6 for all six stats, with optional stat swaps.
2. **Society of Origin** — Choose the polity where your character was raised (Third Imperium, Solomani Confederation, Aslan Hierate, Hiver Federation, Zhodani Consulate, Two Thousand Worlds, Vargr Extents, or Other/Frontier). This filters the species picker to only show species relevant to that society.
3. **Species** — Pick a species from those available in your chosen society; modifiers and traits are applied automatically. Noble titles are granted to high-SOC Third Imperium characters.
3. **Background skills** — Skill picks gated by EDU DM.
4. **Pre-career education** — Optional phase before the career loop (see below).
5. **Career loop** — Qualify → assignment → basic training → skill training → survival → event → mishap (if failed survival) → advancement → end term (aging at term 4+). Repeats for as many careers and terms as the player chooses.
6. **Mustering out** — Cash and benefit rolls from each career's table, with pension calculation for long service.
7. **Skill packages** — Optional package pick at the end of mustering out.
8. **Psionics** — Optional PSI test and talent training (available pre-career or between terms with GM permission).
9. **Finalize** — Capsule description generated, character sheet rendered, PDF/JSON export.

### Pre-career education (7 tracks)

| Track | Requirement | Duration | Notes |
|---|---|---|---|
| **University** | INT 6+ | 4 years (+2 age) | +1 EDU on enrol; graduate for +2 EDU and 2 skills at level 1; Honours adds SOC+1 and DM+1 to first qualification |
| **Military Academy** | Varies by service | 3 years (+1 age) | Service-specific qualification; graduate with Honours for automatic commission rank; full education event table |
| **Merchant Academy** | INT 9+ | 4 years (+2 age) | Business or Shipboard curriculum; graduate for +1 EDU, start Merchant/Citizen at officer rank, permanent advancement DM |
| **Colonial Upbringing** | Homeworld TL ≤ 8 (automatic) | — | Survival 1 + 10 skills at 0; graduate for END+1 and Jack-of-all-Trades 1, but EDU−D3 and permanent qualification penalties |
| **School of Hard Knocks** | SOC ≤ 6 (automatic) | — | Streetwise 1 + 2 skill picks; graduate for Gun Combat 0 + 3 more skills, but DM−2 commission in first career |
| **Spacer Community** | Homeworld size 0, INT 4+ (automatic) | 3 years | Vacc Suit 1 + 2 picks; graduate for DEX+1, Pilot 0, and permanent DM+1 to Merchant (Free Trader) advancement |
| **Psionic Community** | PSI 8+ after test | 3 years | Tests PSI on enrolment; psionic talent training; graduate for PSI+1 and permanent Psion career auto-entry |

Ineligible tracks are always visible in the picker as greyed-out cards explaining the requirement.

### Careers (all 13 fully encoded)

Every career has qualification, all assignments, full skill tables, events (2–12), mishaps (1–6), rank tracks with bonuses, and mustering-out tables.

| Career | Assignments |
|---|---|
| **Agent** | Law Enforcement, Intelligence, Corporate |
| **Army** | Support, Infantry, Cavalry |
| **Citizen** | Corporate, Worker, Colonist |
| **Drifter** | Barbarian, Wanderer, Scavenger |
| **Entertainer** | Artist, Journalist, Performer |
| **Marine** | Support, Star Marine, Ground Assault |
| **Merchant** | Merchant Marine, Free Trader, Broker |
| **Navy** | Line/Crew, Engineer/Gunner, Flight |
| **Noble** | Administrator, Diplomat, Dilettante |
| **Prisoner** | Thug, Fixer, Inmate |
| **Rogue** | Thief, Enforcer, Pirate |
| **Scholar** | Field Researcher, Scientist, Physician |
| **Scout** | Courier, Surveyor, Explorer |

### Events and mishaps — fully auto-applied

All event (2–12) and mishap (1–6) outcomes are mechanically resolved:

- Skill gains, characteristic changes, DM bonuses, and associates (allies/contacts/rivals/enemies) are applied directly to the character.
- **Dual-choice events** present a pick-one UI before continuing.
- **Life Event sub-table** (event 7 in most careers) rolls a second D6 and applies: travel, crime, illegal goods, good fortune, new contact, injury, psionic test, etc.
- **Injury Table** — interactive: when a mishap calls for an injury, the player chooses which characteristic absorbs the damage (where the rules allow a choice). Medical debt is tracked.
- **Career transfers** from events (e.g. Army 10 → Marines without qualification roll) are tracked and honoured.
- **Skill check events** (e.g. Scout event 2) apply the pass or fail branch automatically.
- **Text-only mishaps** (no mechanical effect) are flagged so the player knows nothing further needs resolving.

### Additional rules

- **Commissioning** — Army, Marine, Navy, and Noble careers prompt for a commission roll; officers start at rank 1 and use a separate rank track.
- **Draft** — Failed qualification offers a draft roll (D6 → career assignment).
- **Aging** — From term 4 onward, END/STR/DEX each roll 2D vs. their value; failures apply −1. Anagathics can be purchased to delay aging (addiction risk modelled).
- **Boon rolls** — GM-configurable pool of re-rolls; tracked per character.
- **Noble titles** — SOC 10–15 grants an Imperial title that appears on the character sheet.
- **Anagathics** — Purchase each term to slow aging; tracks addicted status.
- **Connections Rule** — Basic support: a "Connection" button lets the GM note a link to another character (skill grant from the connection is handled manually).
- **GM Mode** — Toggle to manually set every dice roll result, for testing or scripted sessions.
- **NPC generator** — `/api/character/generate-npc` produces a quick stat block without running the full lifepath.

### Species

Species are listed in picker order (set by `sort_order` in each JSON).

| File ID | Name | Key Modifiers | Notes |
|---|---|---|---|
| `imperial_human` | Imperial Human | — | Default; no modifiers |
| `imperial_vargr` | Vargr (Imperial Raised) | STR−1 DEX+1 END−1 | Bite, Heightened Senses |
| `imperial_aslan` | Aslan (Imperial Raised) | STR+2 DEX−2 | Dewclaw, Heightened Senses |
| `imperial_bwap` | Bwap (Imperial Raised) | STR−4 END−4 | Boon on Admin/Science; Bane on psionic test |
| `jonkeereen` | Jonkeereen | END+2 | Desert Survival DM+3; breathe tainted atmo; shorter lifespan |
| `luriani` | Luriani | DEX+1 END+1 SOC−2 | Aquatic Adaptation; Histrionics |
| `sydite` | Sydite | STR+2 END+2 DEX−2 INT−3 EDU−3 | Four-Armed; Resilient (Protection+1); Plodding Along |
| `akeed` | Akeed | STR−2 END−2 INT+1 | Akeed Debate DM+2; Akeed Friendship bond; non-humanoid physiology |
| `capry_female` | Capry — Female | STR−3 DEX+2 END−2 INT+1 | Liberating Fatalism; Third Hand |
| `capry_big_male` | Capry — Big Male | STR−1 END+1 | Liberating Fatalism; Third Hand |
| `capry_small_male` | Capry — Small Male | STR−4 DEX+3 END−3 EDU+2 | Liberating Fatalism; Third Hand |
| `droashav` | Droashav | STR+2 DEX−1 END+3 INT−1 | Six-limbed; Natural Defences (Protection+1, claw 1D+2) |
| `faar` | Faar | INT+1 | Closed Book (DM−2 to read); Homesickness |

---

## Project structure

```
traveller-creator/
├── app/
│   ├── main.py                     # FastAPI routes (~70 endpoints)
│   ├── engine/
│   │   ├── dice.py                 # 2D/1D/D3 rolling, characteristic DMs
│   │   ├── character.py            # Pydantic Character model (JSON-serializable)
│   │   ├── rules.py                # JSON data loader with lru_cache
│   │   └── lifepath.py             # Rules engine (all phases)
│   ├── data/
│   │   ├── species/                # 8 species JSON files
│   │   ├── careers/                # 13 career JSON files (all complete)
│   │   └── tables/
│   │       ├── aging.json
│   │       ├── background_skills.json
│   │       ├── education.json      # Pre-career track definitions
│   │       ├── injury.json
│   │       ├── life_events.json
│   │       ├── mustering_benefits.json
│   │       ├── psionics.json
│   │       ├── skill_packages.json
│   │       └── skills.json         # Canonical skill list
│   ├── templates/
│   │   └── index.html              # Single Jinja2 template
│   └── static/
│       ├── css/style.css           # CRT terminal aesthetic
│       └── js/app.js               # Client-side phase controller (vanilla JS)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── VERSION
└── README.md
```

---

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
  "source": "Traveller Core Rulebook"
}
```

Refresh the browser — it appears in the species picker immediately.

### Adding or editing a career

All 13 careers are complete; use `app/data/careers/scout.json` as the reference schema. Key fields:

- `skill_tables` — `personal_development`, `service_skills`, `advanced_education`, plus one per assignment, each keyed `"1"` through `"6"`
- `ranks` — either `"default"` (one track) or per-assignment, each entry `{"title": "...", "bonus": "..."}`
- `mishaps` — keyed `"1"` through `"6"`, each a text string or structured object
- `events` — keyed `"2"` through `"12"`, with type and effect fields for auto-application
- `mustering_out` — keyed `"1"` through `"7"`, each `{"cash": <credits>, "benefit": "<name>"}`
- `"complete": true` — marks the career as fully playable

### Adding a new pre-career track

Edit `app/data/tables/education.json` to add a new entry under `"tracks"`. The engine reads enrollment skills, graduation benefits (stat gains, skills, permanent DMs), and event table references from this file. For complex multi-round skill picks or conditional eligibility, add a handler branch in `app/engine/lifepath.py → pre_career_qualify()`.

---

## API

All `POST` endpoints accept `{"character": {...}, ...action_params}` and return `{"character": {...}, ...result}`.

### Reference data (GET)

| Endpoint | Returns |
|---|---|
| `/api/species` | List of all species |
| `/api/careers` | Career names and IDs |
| `/api/careers/full` | Full career JSON |
| `/api/background-skills` | Background skill table |
| `/api/skill-packages` | Skill package options |
| `/api/tables/aging` | Aging table |
| `/api/tables/injury` | Injury table |
| `/api/tables/life-events` | Life event table |
| `/api/tables/mustering-benefits` | Universal benefit table |
| `/api/tables/education` | Pre-career education data |
| `/api/tables/psionics` | Psionic talents table |
| `/api/tables/skills` | Canonical skill list |
| `/api/character/generate-npc` | Quick NPC stat block |

### Character creation (POST)

| Endpoint | Purpose |
|---|---|
| `/api/character/new` | Fresh empty character |
| `/api/character/roll-characteristics` | Roll 2D × 6 |
| `/api/character/swap-stats` | Swap two characteristic values |
| `/api/character/apply-species` | Apply species modifiers and traits |
| `/api/character/background-skills` | Grant background skills at level 0 |
| `/api/character/apply-skill-package` | Apply a skill package at finalization |

### Pre-career education (POST)

| Endpoint | Purpose |
|---|---|
| `/api/character/pre-career/qualify` | Enrol in a pre-career track (or attempt qualification) |
| `/api/character/pre-career/graduate` | Roll graduation and apply benefits |
| `/api/character/pre-career/choose-skills` | Confirm skill picks from enrollment/graduation |
| `/api/character/pre-career/any-skill` | Free skill pick from the canonical list |
| `/api/character/pre-career/event` | Roll the education event table |
| `/api/character/pre-career/event10-skill` | Resolve event 10 bonus skill pick |
| `/api/character/pre-career/event11-choice` | Resolve event 11 branch choice |
| `/api/character/pre-career/skip` | Skip pre-career and go straight to careers |

### Careers (POST)

| Endpoint | Purpose |
|---|---|
| `/api/character/qualify` | Career qualification roll |
| `/api/character/draft` | Draft roll (after failed qualification) |
| `/api/character/start-term` | Begin a new term (basic training, rank bonuses) |
| `/api/character/survive` | Survival roll |
| `/api/character/event` | Event table roll and resolution |
| `/api/character/mishap` | Mishap table roll and resolution |
| `/api/character/career-mishap-choice` | Resolve an interactive mishap choice |
| `/api/character/advance` | Advancement roll |
| `/api/character/skill-roll` | Roll on a specific skill table |
| `/api/character/event-skill-grant` | Apply a skill granted by an event |
| `/api/character/event-dm-grant` | Apply a DM bonus granted by an event |
| `/api/character/event-transfer-offer` | Accept/decline a career transfer offer |
| `/api/character/event-stat-change` | Apply a stat change from an event |
| `/api/character/cross-career-roll` | Roll on another career's skill table (event reward) |
| `/api/character/ban-career` | Permanently ban a career (e.g. Scout event 2 failure) |
| `/api/character/associate` | Add an ally, contact, rival, or enemy |
| `/api/character/end-term` | Close term; trigger aging if term 4+ |
| `/api/character/muster-out` | Cash or benefit roll from mustering-out table |
| `/api/character/anagathics` | Purchase anagathics for the current term |
| `/api/character/injury` | Roll on the injury table |
| `/api/character/injury-choice` | Player chooses which stat absorbs injury damage |

### Life events & psionics (POST)

| Endpoint | Purpose |
|---|---|
| `/api/character/life-event` | Roll and resolve the Life Event sub-table |
| `/api/character/life-event-choice` | Resolve an interactive life event choice |
| `/api/character/psionics/test` | Roll PSI test (sets `psi` value) |
| `/api/character/psionics/train` | Train a psionic talent |

### Utility (POST/GET)

| Endpoint | Purpose |
|---|---|
| `/api/character/boon` | Use one boon roll re-roll |
| `/api/character/boon-pool` | Set the boon roll pool size (GM) |
| `/api/character/capsule` | Generate capsule description |
| `/api/character/connection` | Record a character connection |
| `/api/reload-rules` | Flush JSON caches without restart |
| `/api/health` | Sanity check |

---

## Character state

The `Character` object is the single source of truth. It lives in `localStorage`, travels with every API call, and is returned updated. Key fields of note:

| Field | Purpose |
|---|---|
| `phase` | Current creation phase (`characteristics` → `species` → `background` → `pre_career` → `career` → `mustering` → `finalize` → `done`) |
| `pre_career_status` | Transient state during pre-career enrollment (track, stage, skill pool, event roll, etc.) |
| `pre_career_permanent_dms` | Permanent DMs granted by pre-career education (qualification, commission, advancement, auto-rank, etc.) |
| `current_term` | The in-progress career term |
| `term_history` | Every completed term with skills gained, events, survival, advancement |
| `completed_careers` | Summary record per career |
| `pending_life_event_choice` | Populated when a life event needs player input; cleared by `/life-event-choice` |
| `pending_injury_choice` | Populated when the player must choose which stat absorbs injury damage |
| `pending_career_mishap_choice` | Populated when a mishap requires player input |
| `forced_next_career_id` | Set by events/education that mandate a specific next career |
| `pending_transfer_career_id` | Career transfer offer from an event; consumed on next qualification |
| `banned_career_ids` | Careers permanently closed (e.g. Scout event 2 fail) |
| `good_fortune_benefit_dm` | DM+2 tokens from Life Event 10, usable on benefit rolls |

---

## Legal

*Traveller* is a trademark of Far Future Enterprises, used under licence by Mongoose Publishing. The rules reproduced here are from the Mongoose Traveller 2e Core Rulebook; this project is a fan tool for personal use at the table. Rules text in the JSON data files is paraphrased under fair use for game-aid purposes — please own the rulebook.
