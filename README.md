# Traveller Character Creator

A web app for generating Mongoose Traveller 2e characters through the complete lifepath system — characteristics, species, pre-career education, careers (qualify, survive, events, mishaps, advancement, aging), mustering out, psionics, and a final character sheet with capsule description.

Built as a Docker-packaged FastAPI + Jinja2 + vanilla JS stack. All rules data lives in editable JSON files — no code changes required to add a new career, species, or tweak a table.

![Version](https://img.shields.io/badge/version-6.3-blue) ![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Jinja-green) ![Docker](https://img.shields.io/badge/docker-compose%20up-blue)

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
2. **Society of Origin** — Choose the polity where your character was raised (Third Imperium, Solomani Confederation, Aslan Hierate, Hiver Federation, Zhodani Consulate, Two Thousand Worlds, Vargr Extents, or Other/Frontier). Filters the species picker and career list to only show options relevant to that society.
3. **Species** — Pick a species from those available in your chosen society; modifiers and traits are applied automatically. Noble titles granted to high-SOC Third Imperium characters. Solomani characters roll a Heritage Roll (2D) to determine sub-type.
4. **Background skills** — Skill picks gated by EDU DM.
5. **Pre-career education** — Optional phase before the career loop (see below).
6. **Career loop** — Qualify → assignment → basic training → skill training → survival → event → mishap (if failed survival) → advancement → end term (aging at term 4+). Repeats for as many careers and terms as the player chooses.
7. **Mustering out** — Cash and benefit rolls from each career's table. Retirement pension calculated automatically for 5+ terms served.
8. **Skill packages** — Optional package pick at the end of mustering out.
9. **Psionics** — Optional PSI test and talent training (available pre-career or between terms with GM permission).
10. **Finalize** — Capsule description generated, character sheet rendered, PDF/JSON export.

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

Ineligible tracks are visible in the picker as greyed-out cards explaining the requirement.

### Careers (18 fully encoded)

Every career has qualification, all assignments, full skill tables, events (2–12), mishaps (1–6), rank tracks with bonuses, and mustering-out tables.

#### Third Imperium (13)

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

#### Solomani Confederation (5)

| Career | Assignments | Notes |
|---|---|---|
| **Confederation Navy** | Line/Crew, Engineer/Gunner, Flight | Solomani-only; blocked for Imperial characters |
| **Confederation Army** | Support, Infantry, Cavalry | Solomani-only |
| **Star Marines** | Support, Star Marine, Battledress | Solomani-only |
| **Party** | Apparatchik, Functionary, Director | Solomani Party political career |
| **SolSec** | Field Agent, Administration, Secret Agent | Secret Agent uses a cover career for survival/advancement rolls |

Careers with `societies` set are only shown for characters from that polity. Careers with `blocked_societies` are hidden for those characters (e.g. Imperial Navy/Army/Marine/Noble/Scout are hidden for Solomani characters).

### Events and mishaps — fully auto-applied

All event (2–12) and mishap (1–6) outcomes are mechanically resolved:

- Skill gains, characteristic changes, DM bonuses, and associates (allies/contacts/rivals/enemies) are applied directly to the character.
- **Dual-choice events** present a pick-one UI before continuing.
- **Life Event sub-table** (event 7 in most careers) rolls a second D6 and applies: travel, crime, illegal goods, good fortune, new contact, injury, psionic test, etc. Solomani characters use a separate Solomani Life Events table.
- **Injury Table** — interactive: when a mishap calls for an injury, the player chooses which characteristic absorbs the damage. Medical debt is tracked.
- **Career transfers** from events (e.g. Army 10 → Marines without qualification roll) are tracked and honoured.
- **Skill check events** (e.g. Scout event 2) resolve the pass/fail branch correctly — success suppresses any "roll on the Mishap Table" clause in the failure branch.
- **Text-only mishaps** (no mechanical effect) are flagged so the player knows nothing further needs resolving.

### Solomani Confederation mechanics

Characters raised in the Solomani Confederation have additional systems:

- **Heritage Roll** — Picking *Human (Solomani Confederation)* as species triggers a 2D roll that determines sub-type: Non-Solomani (2), Mixed Heritage (3–5), or Racial Solomani (6–12). Each sub-type has different characteristic modifiers and traits.
- **Party Patronage** — Racial Solomani add their SOC DM to all qualification rolls (except Drifter/Prisoner). Mixed Heritage characters take DM−1 to qualification.
- **SolSec Secret Agent cover career** — Secret Agents choose a cover career at term start. Survival uses the cover career's stats at DM−1; advancement uses cover career stats at DM+1. SolSec's own rank table governs promotions.
- **Solomani Draft table** — Confederation Navy, Confederation Army, Star Marines, Merchant, SolSec, Agent (differs from the Imperial table).
- **Home Forces Reserves** — Any eligible Solomani not in a military career may enlist as a part-time planetary defender. Grants a 1D training roll and an auto-0 skill (Gun Combat or Vacc Suit). A natural 2 on survival also triggers a Reserve Mishap roll. Run alongside the character's main career.
- **SolSec Monitor** — Any non-SolSec Solomani may volunteer as a SolSec informer. Grants DM+1 to all advancement rolls (not Drifter). A natural 2 on survival triggers a SolSec Mishap; a natural 12 triggers a SolSec Event and adds a SolSec Contact. Monitor rank rises with career promotions; rank 3+ earns one extra benefit roll at muster-out.

### Additional rules

- **Commissioning** — Army, Marine, Navy, and Noble careers prompt for a commission roll; officers start at rank 1 and use a separate rank track.
- **Draft** — Failed qualification offers a draft roll (D6 → career assignment).
- **Aging** — From term 4 onward, END/STR/DEX each roll 2D vs. their value; failures apply −1. Anagathics can be purchased each term to suppress the aging roll; shortfall credit goes to medical debt (addiction risk modelled).
- **Retirement pension** — Characters leaving with 5+ total terms earn a pension: 5 terms Cr10,000/yr, 6 → Cr12,000, 7 → Cr14,000, 8+ → Cr16,000/yr.
- **Medical debt** — Injuries and anagathics shortfall add to a running debt; cash benefit rolls pay it off automatically.
- **Boon rolls** — GM-configurable pool of re-rolls; tracked per character.
- **Noble titles** — SOC 10–15 grants an Imperial title that appears on the character sheet.
- **Connections Rule** — A "Connection" button lets the GM note a link to another character.
- **GM Mode** — Toggle to manually set every dice roll result, for testing or scripted sessions.
- **NPC generator** — `/api/character/generate-npc` produces a quick stat block without running the full lifepath.

### Species (27 files)

Species are listed in picker order (set by `sort_order` in each JSON) and filtered by the chosen society.

| File ID | Name | Society | Key Modifiers |
|---|---|---|---|
| `imperial_human` | Imperial Human | Third Imperium | — |
| `imperial_vargr` | Vargr (Imperial Raised) | Third Imperium | STR−1 DEX+1 END−1 |
| `imperial_aslan` | Aslan (Imperial Raised) | Third Imperium | STR+2 DEX−2 |
| `imperial_bwap` | Bwap | Third Imperium | STR−4 END−4 |
| `jonkeereen` | Jonkeereen | Third Imperium | END+2 |
| `luriani` | Luriani | Third Imperium | DEX+1 END+1 SOC−2 |
| `sydite` | Sydite | Third Imperium | STR+2 END+2 DEX−2 INT−3 EDU−3 |
| `akeed` | Akeed | Third Imperium | STR−2 END−2 INT+1 |
| `capry_female` | Capry — Female | Third Imperium | STR−3 DEX+2 END−2 INT+1 |
| `capry_big_male` | Capry — Big Male | Third Imperium | STR−1 END+1 |
| `capry_small_male` | Capry — Small Male | Third Imperium | STR−4 DEX+3 END−3 EDU+2 |
| `droashav` | Droashav | Third Imperium | STR+2 DEX−1 END+3 INT−1 |
| `faar` | Faar | Third Imperium | INT+1 |
| `solomani_human` | Human (Solomani Confederation) | Solomani Confederation | Triggers Heritage Roll (2D) |
| `solomani_racial` | Racial Solomani | Solomani Confederation | SOC+1 (resolved by Heritage Roll) |
| `solomani_mixed` | Mixed Heritage Solomani | Solomani Confederation | No modifiers (resolved by Heritage Roll) |
| `confederation_human` | Non-Solomani Human | Solomani Confederation | No modifiers (resolved by Heritage Roll) |
| `zhodani_human` | Zhodani Human | Zhodani Consulate | — |
| `hierate_aslan` | Aslan (Hierate) | Aslan Hierate | STR+2 DEX−2 |
| `extents_vargr` | Vargr (Extents) | Vargr Extents | STR−1 DEX+1 END−1 |
| `hiver_federation_human` | Hiver Federation Human | Hiver Federation | — |
| `two_thousand_worlds_human` | Two Thousand Worlds Human | Two Thousand Worlds | — |
| `sword_worlds_human` | Sword Worlds Human | Other/Frontier | — |
| `frontier_human` | Frontier Human | Other/Frontier | — |

---

## Project structure

```
traveller-creator/
├── app/
│   ├── main.py                     # FastAPI routes (~80 endpoints)
│   ├── engine/
│   │   ├── dice.py                 # 2D/1D/D3 rolling, characteristic DMs, bane rolls
│   │   ├── character.py            # Pydantic Character model (JSON-serializable)
│   │   ├── rules.py                # JSON data loader with lru_cache, society helpers
│   │   └── lifepath.py             # Rules engine (all phases)
│   ├── data/
│   │   ├── species/                # 27 species JSON files
│   │   ├── careers/                # 18 career JSON files (all complete)
│   │   └── tables/
│   │       ├── aging.json
│   │       ├── background_skills.json
│   │       ├── education.json      # Pre-career track definitions
│   │       ├── injury.json
│   │       ├── life_events.json
│   │       ├── solomani_life_events.json
│   │       ├── mustering_benefits.json
│   │       ├── psionics.json
│   │       ├── skill_packages.json
│   │       ├── skills.json         # Canonical skill list
│   │       └── societies.json      # Society definitions and species whitelists
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

To restrict a species to a specific society, add `"societies": ["solomani_confederation"]` (whitelist) or reference the `societies.json` table.

### Adding or editing a career

Use `app/data/careers/scout.json` as the reference schema. Key fields:

- `skill_tables` — `personal_development`, `service_skills`, `advanced_education`, plus one per assignment, each keyed `"1"` through `"6"`
- `ranks` — either `"default"` (one track) or per-assignment, each entry `{"title": "...", "bonus": "..."}`
- `mishaps` — keyed `"1"` through `"6"`, each a text string or structured object
- `events` — keyed `"2"` through `"12"`, with type and effect fields for auto-application
- `mustering_out` — keyed `"1"` through `"7"`, each `{"cash": <credits>, "benefit": "<name>"}`
- `"complete": true` — marks the career as fully playable
- `"societies": ["solomani_confederation"]` — restricts career to characters from that polity
- `"blocked_societies": ["solomani_confederation"]` — hides career for characters from that polity

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
| `/api/character/racial-background-roll` | Roll Heritage (2D) for Solomani human sub-type |
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
| `/api/character/start-term` | Begin a new term; accepts `cover_career_id` for SolSec Secret Agent |
| `/api/character/survive` | Survival roll; triggers parallel Reserve/Monitor events if applicable |
| `/api/character/event` | Event table roll and resolution |
| `/api/character/mishap` | Mishap table roll and resolution |
| `/api/character/career-mishap-choice` | Resolve an interactive mishap choice |
| `/api/character/advance` | Advancement roll; applies Monitor DM+1 if active |
| `/api/character/skill-roll` | Roll on a specific skill table |
| `/api/character/event-skill-grant` | Apply a skill granted by an event |
| `/api/character/event-dm-grant` | Apply a DM bonus granted by an event |
| `/api/character/event-transfer-offer` | Accept/decline a career transfer offer |
| `/api/character/event-stat-change` | Apply a stat change from an event |
| `/api/character/cross-career-roll` | Roll on another career's skill table (event reward) |
| `/api/character/ban-career` | Permanently ban a career (e.g. Scout event 2 failure) |
| `/api/character/associate` | Add an ally, contact, rival, or enemy |
| `/api/character/end-term` | Close term; trigger aging if term 4+; update pension |
| `/api/character/muster-out` | Cash or benefit roll from mustering-out table |
| `/api/character/anagathics` | Purchase anagathics; shortfall added to medical debt |
| `/api/character/injury` | Roll on the injury table |
| `/api/character/injury-choice` | Player chooses which stat absorbs injury damage |
| `/api/character/home-forces` | Enrol in or resign from Home Forces Reserves (`action: "enroll"\|"leave"`) |
| `/api/character/solsec-monitor` | Toggle SolSec Monitor status (`active: true\|false`) |

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

The `Character` object is the single source of truth. It lives in `localStorage`, travels with every API call, and is returned updated. Key fields:

| Field | Purpose |
|---|---|
| `phase` | Current creation phase (`characteristics` → `species` → `background` → `pre_career` → `career` → `mustering` → `finalize` → `done`) |
| `society_id` | Chosen polity; gates career lists, draft table, parallel service options |
| `species_id` | Resolved species (after Heritage Roll for Solomani) |
| `pre_career_status` | Transient state during pre-career enrollment |
| `pre_career_permanent_dms` | Permanent DMs granted by pre-career education |
| `current_term` | The in-progress career term (includes `cover_career_id` for SolSec Secret Agent) |
| `term_history` | Every completed term with skills gained, events, survival, advancement |
| `completed_careers` | Summary record per career |
| `pending_benefit_rolls` | Rolls remaining in the muster-out phase |
| `pension_per_year` | Annual pension in Credits (set when 5+ terms served) |
| `medical_debt` | Outstanding injury/anagathics debt; auto-deducted from cash rolls |
| `home_forces_enrolled` | Whether the character is in the Home Forces Reserves |
| `home_forces_component` | `"groundside"` or `"naval"` |
| `home_forces_rank` | Current reserve rank |
| `solsec_monitor` | Whether the character is an active SolSec Monitor |
| `solsec_monitor_rank` | Monitor rank (rises with career promotions; rank 3+ = extra benefit roll) |
| `pending_life_event_choice` | Populated when a life event needs player input |
| `pending_injury_choice` | Populated when the player must choose which stat absorbs injury damage |
| `pending_career_mishap_choice` | Populated when a mishap requires player input |
| `forced_next_career_id` | Set by events/education that mandate a specific next career |
| `pending_transfer_career_id` | Career transfer offer from an event; consumed on next qualification |
| `banned_career_ids` | Careers permanently closed |
| `good_fortune_benefit_dm` | DM+2 tokens from Life Event 10, usable on benefit rolls |

---

## Legal

*Traveller* is a trademark of Far Future Enterprises, used under licence by Mongoose Publishing. The rules reproduced here are from the Mongoose Traveller 2e Core Rulebook and the Solomani Rim sourcebook; this project is a fan tool for personal use at the table. Rules text in the JSON data files is paraphrased under fair use for game-aid purposes — please own the rulebook.
