# Traveller Character Creator

A web app for generating Mongoose Traveller 2e characters through the complete lifepath system — characteristics, species, pre-career education, careers (qualify, survive, events, mishaps, advancement, aging), mustering out, psionics, and a final character sheet with capsule description. Supports background packages and career packages as streamlined one-step alternatives to the traditional lifepath phases.

Built as a Docker-packaged FastAPI + Jinja2 + vanilla JS stack. All rules data lives in editable JSON files — no code changes required to add a new career, species, or tweak a table.

![Version](https://img.shields.io/badge/version-19.2-blue) ![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Jinja-green) ![Docker](https://img.shields.io/badge/docker-compose%20up-blue)

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

1. **Characteristics** — Roll 2D×6 for all six stats, with optional stat swaps. Heroic mode rolls 4×2D normally and 2×3D6 drop-lowest for the highest two. Optional extra characteristics (PSI, WLT, LCK, MRL, STY, TER) can be toggled on and rolled separately with the same heroic option.
2. **Society of Origin** — Choose the polity where your character was raised (Third Imperium, Solomani Confederation, Aslan Hierate, Hiver Federation, Zhodani Consulate, Two Thousand Worlds, Vargr Extents, or Other/Far Domains). Filters the species picker and career list to only show options relevant to that society.
3. **Species** — Pick a species from those available in your chosen society; modifiers and traits are applied automatically. Noble titles granted to high-SOC Third Imperium characters. Solomani characters roll a Heritage Roll (2D) to determine sub-type. Cetacean species (Dolphin, Orca) set a species-specific starting age.
4. **Background skills** — Skill picks gated by EDU DM, or take a **Background Package** (see below) for a curated skill bundle in lieu of individual picks.
5. **Pre-career education** — Optional phase before the career loop (see below).
6. **Career loop** — Qualify → assignment → basic training → skill training → anagathics offer → survival → event → mishap (if failed survival) → advancement → end term (aging at species-appropriate term). Repeats for as many careers and terms as the player chooses. On the **first** career pick only, a **Career Package** can be chosen instead (see below) — skips the loop entirely and goes straight to finalization.
7. **Mustering out** — Cash and benefit rolls per career. Each career's roll allowance is terms served + rank bonus (ranks 1–2: +1, ranks 3–4: +2, ranks 5+: +3). Retirement pension calculated automatically for 5+ terms served.
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

### Background Packages (alternative to background skills)

At the background phase the player may choose a **Background Package** instead of picking individual background skills. Each package represents a specific upbringing and grants a curated set of skills, starting credits, and (for some packages) stat adjustments — no EDU gating, no individual picks required.

| Package | Highlights |
|---|---|
| **Belter** | Vacc Suit, Zero-G, Mechanic, Astrogation 0; Cr2,000 |
| **Criminal** | Stealth, Streetwise, Deception; Cr1,000 |
| **Drifter** | Survival, Recon, Athletics (endurance); Cr500 |
| **Farmer** | Animals, Survival, Athletics (endurance); Cr2,000 |
| **Merchant Family** | Broker, Persuade, Admin; Cr3,000 |
| **Military Family** | Athletics, Gun Combat 0, Melee 0, Discipline; Cr1,000 |
| **Noble Birth** | Admin, Carouse, Diplomat, Persuade; SOC+1; Cr5,000 — requires SOC 10+ |
| **Primitive** | Survival, Animals, Recon; STR+1, END+1, EDU−1; Cr200 |
| **Scholar Family** | Science 0, Electronics (computers), Investigate; Cr2,000 |
| **Spacer** | Vacc Suit, Mechanic, Pilot (small craft); Cr1,500 |
| **Street Kid** | Streetwise, Stealth, Athletics (dexterity); Cr500 |
| **Technical** | Mechanic, Electronics 0, Engineer 0; Cr2,500 |

Choosing a background package is recorded in `pre_career_status.track = "background_package"` and appears in the career narrative capsule.

### Career Packages (alternative to the career loop)

On the **first** career pick only, a **Career Package** button appears in the career picker. Choosing it bypasses the qualify/survive/advance loop entirely. The player:

1. Selects one of 17 packages representing a complete pre-defined career.
2. Rolls d3 and adds the result to their age.
3. Picks one option from each of three finalising categories:

| Category | Choices |
|---|---|
| **CAREER** | Boost one skill to level 4 · Boost three skills by +1 each · Take rank 4 only |
| **TRAVELLER SKILLS** | One of 12 pairs of useful traveller skills (e.g. Vacc Suit + Steward, Pilot (any) + Astrogation, …) |
| **BENEFITS** | 1 Ship Share · Cr100,000 cash · Combat Implant · 1 Ally + 2 Contacts · TAS Membership · SOC +1 |

The character goes directly to finalization (skill package phase) — no further careers can be added.

| Package | Rank | Notes |
|---|---|---|
| **Barbarian** | 2 | STR+1, END+1; Survival, Melee, Recon |
| **Bounty Hunter** | — | Gun Combat, Investigate, Deception, Pilot |
| **Corsair** | 2 | SOC−2; Gunner, Melee, Pilot, Astrogation; 1 Ship Share base |
| **Corporate Executive** | 4 | EDU+1, SOC+1; Admin, Advocate, Broker, Leadership |
| **Doctor** | — | EDU+1; Medic 3, Science, Admin |
| **Drifter** | — | Survival, Streetwise, Recon, Mechanic |
| **Explorer** | 3 | Recon, Survival, Pilot, Astrogation, Navigation |
| **Merchant Captain** | 4 | Pilot, Broker, Admin, Astrogation; 2 Ship Shares base |
| **Military Officer** | 4 | Gun Combat 2, Leadership 2, Tactics; END+1 |
| **Noble** | 4 | SOC+2 (min SOC 10); Admin, Advocate, Carouse, Diplomat |
| **Pilot** | 2 | Pilot 3, Astrogation, Mechanic, Vacc Suit |
| **Rogue** | 2 | Gun Combat, Stealth, Deception, Streetwise |
| **Scholar** | — | EDU+1; Science 3, Science 1, Investigate, Computer |
| **Scout** | 3 | Astrogation 2, Pilot, Recon, Survival, Vacc Suit |
| **Soldier** | 3 | END+1; Gun Combat 2, Melee, Heavy Weapons, Athletics |
| **Technician** | — | Mechanic 2, Electronics 2, Engineer; EDU+1 |
| **Wanderer** | — | Survival, Recon, Stealth, Streetwise |

Career package choices are stored in `career_package_id` and `career_package_taken` on the character. The capsule narrative describes the package career in place of the normal career-loop paragraphs.

### Careers (64 fully encoded)

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
| **Confederation Navy** | Line/Crew, Engineer/Gunner, Flight | Solomani-only; separate officer rank table |
| **Confederation Army** | Support, Infantry, Cavalry | Solomani-only |
| **Star Marines** | Support, Star Marine, Battledress | Solomani-only |
| **Party** | Apparatchik, Functionary, Director | Solomani Party political career |
| **SolSec** | Field Agent, Administration, Secret Agent | Secret Agent uses a cover career for survival/advancement rolls |

#### Cetacean (4)

| Career | Assignments | Species |
|---|---|---|
| **Dolphin Civilian** | Liaison, Nomad, Historian-Poet | Dolphin + Orca |
| **Dolphin Military** | Sea Patrol, Underwater Commando, Guardian | Dolphin + Orca |
| **Philosopher-Elder** | Philosopher-Elder | Orca only |
| **Spirit Singer** | Spirit Singer | Orca only |

Cetacean careers are only shown for Dolphin and Orca characters. Core careers require Vacc Suit first.

#### Bounty Hunter (1, any society)

| Career | Assignments |
|---|---|
| **Bounty Hunter** | Tech Ops, Hunter, Fixer |

Available to characters from any society.

#### Aslan Hierate (11)

| Career | Assignments | Notes |
|---|---|---|
| **Ceremonial** | Poet, Clan Agent, Priest | Also available in Glorious Empire |
| **Envoy** | Negotiator, Spy, Duellist | Also available in Glorious Empire |
| **Management** | Corporate, Clan Aide, Governess | Female-dominant career |
| **Military** | Warrior, Cavalry, Flyer, Support | Male-dominant career |
| **Military Officer** | Leader, Executive Officer, Assassin | Male-dominant career |
| **Outcast** | Labourer, Trader, Scavenger | Hierate only |
| **Outlaw** | Pirate, Raider, Thief | Hierate only |
| **Scientist** | Healer, Researcher, Explorer | Hierate only |
| **Space Officer** | Commander, Shipmaster, Navigator | Male-dominant career |
| **Spacer** | Pilot, Gunner, Engineer, Crew | Hierate only |
| **Wanderer** | Belter, Nomad, Scout | Hierate only |

Career access depends on the character's gender and the role structure of each career. Males are steered toward warrior and technical roles; females toward management and social roles.

#### Glorious Empire (8)

The Glorious Empire shares two careers with the Hierate (Ceremonial, Envoy) and adds six of its own:

| Career | Assignments | Notes |
|---|---|---|
| **Ceremonial** | Poet, Clan Agent, Priest | Shared with Hierate |
| **Envoy** | Negotiator, Spy, Duellist | Shared with Hierate |
| **Fleet** | Pilot, Gunner, Engineer, Crew | GE exclusive |
| **Fleet Officer** | Commander, Shipmaster, Navigator | GE exclusive |
| **Landless One** | Labourer, Wildcatter, Trader, Slaver | GE exclusive |
| **Slave** | Labourer, Servant, Technician, Dog Soldier | GE exclusive |
| **Warrior** | Imperial Guard, Dragoon, Support | GE exclusive |
| **Warrior Officer** | Leader, Executive Officer, Assassin | GE exclusive |

#### K'kree (4)

| Career | Assignments | Notes |
|---|---|---|
| **Merchant (K'kree)** | Mercantile/Economic, Warrior, Technical/Scientific, Naval | SOC 8+ required |
| **Noble (K'kree)** | Warrior, Mercantile/Economic, Technical/Scientific, Naval | SOC 10+ required |
| **K'kree (Pastoral)** | Pastoral | Low-SOC default career |
| **Servant (K'kree)** | Service, Warrior | |

Career access depends on `kkree_soc_rank_degree` (rankholder / kinsman / servant of rankholder), which is derived from SOC at the start of the career loop.

#### Zhodani Consulate (9)

| Career | Assignments | Notes |
|---|---|---|
| **Agent (Zhodani)** | Tozjabr, Thought Police | SOC 10+ required; Thought Police requires PSI 9+ |
| **Army (Zhodani)** | Cavalry, Infantry, Support | Enlisted + officer rank tracks; auto-commission if SOC 10+ |
| **Entertainer (Zhodani)** | Artist, Author, Performer | |
| **Government (Zhodani)** | Administrator, Diplomat | Proles and Intendants max rank 3 |
| **Guard (Zhodani)** | Commandos, Ground Assault, Support | SOC 10+ required; all-commissioned; Commandos requires PSI 9+ |
| **Merchant (Zhodani)** | Broker, Corporate, Free Trader | |
| **Navy (Zhodani)** | Crew, Flight, Technical | Enlisted + officer rank tracks; auto-commission if SOC 10+ |
| **Prole (Zhodani)** | Colonist, Corporate, Worker | SOC 9− only; uses standard Core life events table |
| **Scholar (Zhodani)** | Field Researcher, Lab Scientist, Physician | |

All Zhodani careers except Prole include a **Psionic Skills** table (SOC 10+ only). Army and Navy have the **Officer Skills** table (commissioned characters only). See Zhodani mechanics below.

#### Vargr Extents (11)

| Career | Assignments |
|---|---|
| **Army (Vargr)** | Infantry, Cavalry, Support |
| **Citizen (Vargr)** | Corporate, Aide, Worker |
| **Corsair** | Raider, Pilot, Reaver |
| **Emissary** | Arbitrator, Diplomat, Negotiator |
| **Law Enforcement (Vargr)** | Enforcer, Investigator, Security |
| **Loner** | Hunter, Prospector, Explorer |
| **Marines (Vargr)** | Marine, Special Ops, Support |
| **Merchant (Vargr)** | Junk Dealer, Scrounger, Free Trader |
| **Navy (Vargr)** | Pilot, Crew, Engineer |
| **Psion (Vargr)** | Wild Talent, Mentored, Institute |
| **Scientist (Vargr)** | Doctor, Researcher, Technician |

See Vargr Extents mechanics below.

---

### Events and mishaps — fully auto-applied

All event (2–12) and mishap (1–6) outcomes are mechanically resolved:

- Skill gains, characteristic changes, DM bonuses, and associates (allies/contacts/rivals/enemies) are applied directly to the character.
- **Dual-choice events** present a pick-one UI before continuing.
- **Life Event sub-table** — careers use the standard 2D table; Solomani careers use a separate Solomani Life Events table; Vargr Extents careers use the Vargr Life Events table (with Pack Events 1D sub-table); Zhodani Consulate careers (except Prole) use the Zhodani Life Events table (with Re-education Events 1D sub-table); characters from Drinax (Floating Palace), Drinax (Wasteland), and Asim use homeworld-specific 1D tables with fully auto-applied effects.
- **Injury Table** — when a mishap calls for an injury, the player chooses which characteristic absorbs the damage. Medical debt is tracked.
- **Forced careers** — if a life event, mishap, or anagathics roll mandates a specific next career (e.g. Prisoner), the Decide phase replaces the normal muster-out/continue buttons with a mandatory "Serve Your Sentence" path. Voluntary muster-out is also blocked at the API level.
- **Career transfers** from events are tracked and honoured.
- **Skill check events** resolve the pass/fail branch correctly.
- **Frozen Watch** (Confederation Navy mishap 2) — character stays in service rather than mustering out; term is logged as cryo.

### Skill handling

- **Cascade skills** (Electronics, Science, Gun Combat, Melee, Pilot, Tactics, and 9 others) prompt for a specialty when rolled from a career table without one already specified.
- Skill gains display as `+1 SkillName (level N)` or `+1 SkillName → now level N` so it is always clear the gain is an increment, not a target level.
- Advancement bonus skills are shown immediately on the promotion result screen, not just in the log.
- **Muster-out skill choices** — benefits of the form "Advocate 1 or Broker 1 or Profession 1" present buttons for each option; the chosen skill is applied immediately.

### Commission and rank titles

Military careers (Army, Marine, Navy, Confederation equivalents, Zhodani Army/Navy/Guard) display the correct **officer** rank title after commissioning. Rank titles update on each promotion throughout the career.

### Solomani Confederation mechanics

- **Heritage Roll** — picking *Human (Solomani Confederation)* triggers a 2D roll: Non-Solomani (2), Mixed Heritage (3–5), or Racial Solomani (6–12). Each sub-type has different modifiers and career privileges.
- **Party Patronage** — Racial Solomani add SOC DM to all qualification rolls. Mixed Heritage take DM−1.
- **SolSec Secret Agent cover career** — survival uses cover career stats at DM−1; advancement at DM+1.
- **Solomani Draft table** — separate table from the Imperial draft.
- **Home Forces Reserves** — eligible Solomani characters may enlist alongside their main career for training rolls and parallel survival checks.
- **SolSec Monitor** — non-SolSec Solomani may volunteer as an informer for advancement DMs and bonus benefit rolls.

### Zhodani Consulate mechanics

- **PSI roll at creation** — Zhodani characters roll 2D for PSI immediately after species selection, before any career begins.
- **Social class** — Three classes based on SOC and PSI:
  - *Prole* (SOC 9−) — no access to Psionic Skills tables; careers capped at certain ranks; uses standard Core life events
  - *Intendant* (SOC 10) — Psionic Skills tables available; if PSI 9+ is rolled at creation, a Prole is automatically elevated to Intendant
  - *Noble* (SOC 11+) — full career access; EDU raised to minimum 8 at creation
- **Characteristic adjustments** — at creation: EDU cannot exceed SOC; if SOC 10+ and EDU < 8, EDU is raised to 8.
- **No career-change penalty** — Zhodani characters do not accumulate the −1 DM per previously failed qualification that Imperial characters do.
- **Psionic Skills table** — each non-Prole career includes a fourth specialist table usable by SOC 10+ characters only. Skills include Awareness, Clairvoyance, Telepathy, Telekinesis, Teleportation, and PSI+1.
- **Officer Skills table** — Army and Navy include a commissioned-only specialist table with Admin, Advocate, Diplomat, Leadership, and Tactics.
- **Re-education Events** — certain mishaps and the life event Crime (result 11) trigger a 1D Re-education Events sub-table. Results range from exoneration (extra benefit roll) to two-term re-education with mandatory career change and stat loss.
- **Zhodani draft table** — failed qualification drafts into Army (Infantry), Merchant (Corporate), or Navy (Crew).
- **Noble titles** — SOC 10–15 grants Zhodani titles: Intendant (−iepr), Aspirant (−atl), Wellborn (−stebr), Highborn (−tlas), Noble Born (−tlasche'), Princely Lord (−iashav).

### Aslan Hierate and Glorious Empire mechanics

- **Gender** — Aslan characters must choose a gender (male / female) before the career loop begins. Gender gates career access: males are directed toward military, spacer, and outlaw careers; females toward management, ceremonial, and envoy careers.
- **Clan setup** — After species selection, Hierate Aslan go through a four-phase background setup: clan type roll, ancestral deeds roll (gives a DM modifier), territory type roll, and family position roll. Glorious Empire Aslan skip the clan roll (clan is always Tokouea'we) but otherwise follow the same path.
- **Rite of Passage** — A scored rite-of-passage roll is made during setup. The rite score affects the first career qualification roll.
- **TER (Territorial) characteristic** — Hierate and Glorious Empire Aslan require the TER extra characteristic. TER is rolled at character creation alongside the core six stats. It functions as a measure of territorial holdings and status among Aslan and is used in social checks with other Aslan.
- **Clan Shares** — Aslan accumulate clan_shares instead of (or in addition to) ship shares from mustering-out tables. Clan Shares represent a stake in clan land, territory, or starship assets.
- **Intolerant (Glorious Empire only)** — Glorious Empire Aslan cannot easily gain the Tolerance skill. Event rolls of Tolerance must be re-rolled; only on a second consecutive roll may the skill be taken. Any event that would award Tolerance may award Diplomat instead.

### K'kree mechanics

- **Family patriarch** — A K'kree Traveller is always the patriarch (male head) of a family group, not a solo individual. Character creation generates the patriarch's skills and characteristics; `kkree_wives` and `kkree_family_members` track the size and composition of the family.
- **Background skills** — K'kree always start with Melee 0, Patriarchy 0, Recon 0, and Survival 0 regardless of background skill picks.
- **Social caste** — `kkree_soc_rank_degree` (determined from SOC at the start of the career loop) controls career access:
  - `servant_of_rankholder` (SOC < 6) — only Servant and Pastoral careers
  - `kinsman_of_rankholder` (SOC 6–9) — Merchant or Servant careers
  - `rankholder` (SOC 10+) — Noble or Merchant careers
- **Specialist area** — At the start of the first career a specialty area is rolled (warrior / mercantile / technical / naval), stored in `kkree_specialist_area`. This biases assignment selection throughout the career loop.
- **Claustrophobia and gregariousness** — K'kree traits are tracked on the character sheet and generate in-play notes; they do not add mechanical modifiers to the character builder itself, but are reflected in capsule narrative and the species traits panel.

### Vargr Extents mechanics

- **CHA replaces SOC** — Vargr SOC is labeled CHA (Charisma) in the UI. It is re-rolled as 1D+2 at species selection rather than using the standard 2D roll, reflecting how Vargr charisma is more volatile than Imperial social standing.
- **No career-change penalty** — Vargr do not accumulate the −1 DM per previously failed qualification, representing the ease with which Vargr change employers and pack allegiances.
- **Background skill** — All Vargr Extents characters start with Melee (Infighting) 0.
- **Pack Events** — The Vargr Life Events table results 6 and 8 both trigger a 1D Pack Events sub-table. Results cover pack failure (SOC−1), leaving a pack (re-qualification roll), joining a pack, power struggles (ally or rival), success (SOC+1), and leadership challenges (Leadership or SOC 10+ to take charge).
- **Vargr draft table** — failed qualification drafts into Army (Infantry), Marines, Navy (Crew), or Law Enforcement (Enforcer).

### Additional rules

- **Commissioning** — Army, Marine, Navy, and Noble careers prompt for a commission roll. Officer rank titles replace enlisted titles on success.
- **Draft** — Failed qualification offers a draft roll (1D → career assignment). Draft table varies by society (Imperial, Solomani, Vargr, Zhodani).
- **Aging** — Triggered at a species-specific term (default term 4; Dolphins term 2). Physical reductions are player-chosen; mental reductions auto-applied. Anagathics follow MgT2e RAW: opt-in at first career entry, roll SOC 10+ each term to secure supply, costs 1D×Cr25,000 added to medical debt, active treatment provides a positive aging DM equal to terms used, a natural 2 forces Prisoner career next term.
- **Retirement pension** — 5 terms: Cr10,000/yr; 6→Cr12,000; 7→Cr14,000; 8+→Cr16,000/yr.
- **Medical debt** — Injuries and anagathics shortfall add to a running debt; cash benefit rolls pay it off automatically.
- **Muster-out benefit rolls** — each career grants 1 roll per term served plus a rank bonus (rank 1–2: +1, ranks 3–4: +2, ranks 5+: +3). Career cards show the full breakdown; exhausted careers are disabled so the UI never reaches a dead-end.
- **Noble titles** — SOC 10–15 grants an Imperial title shown on the character sheet. Zhodani characters use Consulate titles instead.
- **Connections Rule** — Links this Traveller to another PC or NPC; each connection can grant +1 in any skill per GM approval.
- **GM Mode** — Toggle to set any dice roll result manually.
- **NPC generator** — One click produces a complete NPC via `GET /api/character/generate-npc`. The generator rolls characteristics, applies a randomly chosen background package, then applies a randomly chosen career package (Noble filtered out if SOC < 10), with all finalising choices made randomly. Returns a fully fleshed character ready for use at the table.

### UI features

- **Mobile layout** — Three-tab navigation (CHARACTER / ACTION / LOG) for small screens. Panels switch on tab click; active tab auto-switches to ACTION after every roll.
- **Light/dark theme** — ◐ button in the header toggles between the default dark amber CRT look and a white/green terminal theme. Preference is saved to `localStorage`.
- **Font size** — "Aa" button in the header cycles Normal → Large → Extra Large. Scales body text, headings, stat values, and buttons. Preference is saved to `localStorage`.
- **Heroic rolls** — ⚔ HEROIC toggle on the characteristics screen; rolls 4 stats with 2D and 2 stats with 3D6 drop-lowest. Mechanic is shown below the button.
- **Optional characteristics** — Toggle shows checkboxes for PSI / WLT / LCK / MRL / STY / TER. Select any combination and roll them separately, with heroic option.

### Species (34)

Species are listed in picker order (`sort_order` in each JSON) and filtered by society. Single-click a card to preview traits; double-click (or click Confirm) to apply.

#### Third Imperium (15)

| Species | Modifiers |
|---|---|
| **Imperial Human** | — |
| **Vargr (Imperial Raised)** | DEX +1, END −1, STR −1 |
| **Aslan (Imperial Raised)** | STR +2, DEX −2 |
| **Bwap** | STR −4, END −4 |
| **Jonkeereen** | END +2 |
| **Luriani** | DEX +1, END +1, SOC −2 |
| **Sydite** | STR +2, END +2, DEX −2, INT −3, EDU −3 |
| **Akeed** | INT +1, STR −2, END −2 |
| **Capry (Female)** | DEX +2, INT +1, STR −3, END −2 |
| **Capry (Big Male)** | END +1, STR −1 |
| **Capry (Small Male)** | DEX +3, EDU +2, STR −4, END −3 |
| **Droashav** | STR +2, END +3, DEX −1, INT −1 |
| **Faar** | INT +1 |
| **Caprisap (Alpine)** | DEX +2, STR −2 |
| **Caprisap (Boar)** | DEX +1, STR −1 |

#### Cetacean (2, any society)

| Species | Modifiers | Notes |
|---|---|---|
| **Uplifted Dolphin** | STR +4, END +2, SOC −4 | Start age 12 · Aging from term 2 |
| **Uplifted Orca** | STR +8, END +4, SOC −4 | Start age 18 · Aging from term 4 |

Cetacean characters need Vacc Suit before most core careers become available; dolphin/orca-exclusive careers are available immediately.

#### Solomani Confederation (4)

| Species | Notes |
|---|---|
| **Human (Solomani)** | Triggers a Heritage Roll (2D) to determine sub-type |
| **Racial Solomani** | SOC +1; SOC DM added to all qualification rolls |
| **Mixed Heritage** | No mods; DM−1 to Confederation career advancement |
| **Non-Solomani Human** | No mods; Party career closed |

#### Aslan Hierate / Glorious Empire (2)

| Species | Modifiers | Notes |
|---|---|---|
| **Aslan (Hierate)** | STR +2, DEX −2 | Dewclaw · Heightened Senses · Honour Bound · Land Sense; starts age 14; aging from term 6; TER characteristic required; accumulates Clan Shares |
| **Aslan (Glorious Empire)** | STR +2, DEX −2 | As Hierate plus Intolerant trait; fixed Tokouea'we clan; access to GE-exclusive careers |

#### Zhodani Consulate (1)

| Species | Modifiers | Notes |
|---|---|---|
| **Zhodani** | — | Biologically human; PSI rolled 2D at creation; social class (Noble/Intendant/Prole) determined by SOC and PSI; characteristic adjustments applied at creation |

#### Vargr Extents (1)

| Species | Modifiers | Notes |
|---|---|---|
| **Vargr (Extents Raised)** | STR −2, DEX +1, END −1 | SOC replaced by CHA (re-rolled 1D+2); Melee (Infighting) 0 background skill; no career-change penalty |

#### Two Thousand Worlds / K'kree (2)

| Species | Society | Modifiers |
|---|---|---|
| **Hiver Federation Human** | Hiver Federation | INT +1, EDU +1 |
| **Two Thousand Worlds Human** | Two Thousand Worlds | END +1, SOC −1 |
| **K'kree** | Two Thousand Worlds | STR +6, INT +2, EDU +2 |

K'kree characters are the patriarch of a family group. They are centauroid obligate herbivores with Claustrophobic and Gregarious traits that generate narrative notes throughout play. Starting age 14; aging from term 6. See K'kree mechanics above.

#### Other / Far Domains (5)

| Species | Modifiers | Background |
|---|---|---|
| **Sword Worlder** | STR +1, END +1, SOC −1 | Norse-influenced frontier worlds; Warrior Culture and Imperial Wariness traits |
| **Frontier Human** | END +1, SOC −1 | Independent systems; Frontier-Bred and Independent Streak traits |
| **Drinax Noble (Floating Palace)** | STR −1, END −1, EDU +1, SOC +1 | Kingdom of Drinax court; Court Education and Decaying Grandeur traits; homeworld 1D life events table |
| **Vespexer (Drinax Wasteland)** | END +2, EDU −1, SOC −1 | Blasted surface of Drinax; Wasteland Survivor and Hatred of the Aslan traits; homeworld 1D life events table |
| **Asim Local** | END +1, EDU −1 | Asim agricultural world; Agricultural World and Foundation Shadow traits; homeworld 1D life events table |

---

## Project structure

```
traveller-creator/
├── app/
│   ├── main.py                     # FastAPI routes
│   ├── engine/
│   │   ├── dice.py                 # 2D/1D/D3 rolling, characteristic DMs
│   │   ├── character.py            # Pydantic Character model (JSON-serializable)
│   │   ├── rules.py                # JSON loader with lru_cache, society helpers
│   │   └── lifepath.py             # Rules engine (all phases)
│   ├── data/
│   │   ├── species/                # 34 species JSON files
│   │   ├── careers/                # 64 career JSON files
│   │   └── tables/
│   │       ├── aging.json
│   │       ├── background_packages.json    # 12 background packages
│   │       ├── background_skills.json
│   │       ├── career_packages.json        # 17 career packages + finalising tables
│   │       ├── education.json              # Pre-career track definitions
│   │       ├── injury.json
│   │       ├── life_events.json            # Standard (Third Imperium) 2D table
│   │       ├── solomani_life_events.json
│   │       ├── vargr_extents_life_events.json   # Includes Pack Events 1D sub-table
│   │       ├── zhodani_life_events.json         # Includes Re-education Events 1D sub-table
│   │       ├── drinax_palace_life_events.json
│   │       ├── drinax_wasteland_life_events.json
│   │       ├── asim_life_events.json
│   │       ├── mustering_benefits.json
│   │       ├── psionics.json
│   │       ├── skill_packages.json
│   │       ├── skills.json                 # Canonical skill list
│   │       └── societies.json             # Society definitions and species whitelists
│   ├── templates/
│   │   └── index.html              # Single Jinja2 template
│   └── static/
│       ├── css/style.css           # CRT terminal aesthetic; light theme; font-size scales
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
  "sort_order": 900,
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

Optional fields:

| Field | Purpose |
|---|---|
| `"societies": [...]` | Restrict to specific polity IDs |
| `"life_events_table": "my_table"` | Use a custom 1D life events JSON file (see `tables/drinax_palace_life_events.json` for format) |
| `"starting_age": 12` | Override starting age (default 18) |
| `"aging_starts_term": 2` | Override when aging begins (default 4) |
| `"blocked_careers": [...]` | Careers always hidden for this species |
| `"allowed_species_careers": [...]` | Career IDs exclusive to this species |
| `"university_dm": -1` | DM applied to university qualification |
| `"military_academy_dm": 1` | DM applied to military academy qualification |
| `"career_qualify_dms": {"scout": 1}` | Per-career qualification bonuses |
| `"uses_clan_shares": true` | Aslan: accumulate Clan Shares from mustering-out instead of (or in addition to) Ship Shares |
| `"extra_characteristics_required": ["TER"]` | Force one or more extra characteristics to be rolled during character creation |
| `"aging_dm_multiplier": 2` | Multiplier applied to aging DMs |
| `"uses_kkree_family": true` | K'kree: enable family-patriarch mechanic |
| `"background_skills": ["Melee 0", ...]` | Override the normal background-skills phase with a fixed species skill list |
| `"uses_cha": true` | Replace SOC label with CHA; re-roll as 1D+2 at creation (Vargr Extents) |
| `"no_career_change_penalty": true` | Skip the −1 DM per failed qualification penalty |
| `"rolls_psi_at_start": true` | Roll 2D for PSI before career selection (Zhodani) |

### Adding or editing a career

Use `app/data/careers/scout.json` as the reference schema. Key fields:

- `skill_tables` — `personal_development`, `service_skills`, `advanced_education`, plus one per assignment, each keyed `"1"` through `"6"`
- `ranks` — either `"default"` (one track), `"enlisted"` + `"officer"` (commissioned careers), or per-assignment; each entry `{"title": "...", "bonus": "..."}`
- `mishaps` — keyed `"1"` through `"6"`, text string or structured object with effects
- `events` — keyed `"2"` through `"12"`, with type and effect fields for auto-application
- `mustering_out` — keyed `"1"` through `"7"`, each `{"cash": <credits>, "benefit": "<name>"}`
- `"complete": true` — marks the career as fully playable
- `"societies": [...]` — restricts career to characters from those polities
- `"blocked_societies": [...]` — hides career for those polities
- `"allowed_species": [...]` — restricts career to listed species only
- `"blocked_species": [...]` — hides career for listed species

### Adding a new pre-career track

Edit `app/data/tables/education.json` to add a new entry under `"tracks"`. The engine reads enrollment skills, graduation benefits, and event table references from this file. For complex eligibility or multi-round skill picks, add a handler branch in `app/engine/lifepath.py → pre_career_qualify()`.

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
| `/api/tables/background-packages` | Background package definitions |
| `/api/tables/career-packages` | Career package definitions + finalising tables |
| `/api/character/generate-npc` | Quick NPC stat block — background + career package, all random |

### Character creation (POST)

| Endpoint | Purpose |
|---|---|
| `/api/character/new` | Fresh empty character |
| `/api/character/roll-characteristics` | Roll 2D × 6 |
| `/api/character/roll-extra-characteristics` | Roll optional extra stats (PSI/WLT/LCK/MRL/STY/TER) |
| `/api/character/swap-stats` | Swap two characteristic values |
| `/api/character/apply-species` | Apply species modifiers and traits |
| `/api/character/racial-background-roll` | Heritage Roll (2D) for Solomani sub-type |
| `/api/character/background-skills` | Grant background skills at level 0 |
| `/api/character/background-package` | Apply a background package in lieu of individual skill picks |
| `/api/character/apply-skill-package` | Apply a skill package at finalization |

### Pre-career education (POST)

| Endpoint | Purpose |
|---|---|
| `/api/character/pre-career/qualify` | Enrol in a pre-career track |
| `/api/character/pre-career/graduate` | Roll graduation and apply benefits |
| `/api/character/pre-career/choose-skills` | Confirm skill picks |
| `/api/character/pre-career/any-skill` | Free skill pick from the canonical list |
| `/api/character/pre-career/event` | Roll the education event table |
| `/api/character/pre-career/event10-skill` | Resolve event 10 bonus skill pick |
| `/api/character/pre-career/event11-choice` | Resolve event 11 branch choice |
| `/api/character/pre-career/skip` | Skip pre-career |

### Careers (POST)

| Endpoint | Purpose |
|---|---|
| `/api/character/qualify` | Career qualification roll |
| `/api/character/career-package` | Apply a career package (first career only; skips loop, goes to finalization) |
| `/api/character/draft` | Draft roll after failed qualification |
| `/api/character/start-term` | Begin a new term |
| `/api/character/survive` | Survival roll |
| `/api/character/event` | Event table roll and resolution |
| `/api/character/mishap` | Mishap table roll and resolution |
| `/api/character/career-mishap-choice` | Resolve an interactive mishap choice |
| `/api/character/commission` | Commission roll (Army / Marine / Navy) |
| `/api/character/advance` | Advancement roll |
| `/api/character/skill-roll` | Roll on a specific skill table |
| `/api/character/apply-specialty` | Apply a specialty choice for a cascade skill (e.g. Electronics → Computers) |
| `/api/character/event-skill-grant` | Apply a skill granted by an event |
| `/api/character/event-dm-grant` | Apply a DM bonus from an event |
| `/api/character/event-transfer-offer` | Accept/decline a career transfer offer |
| `/api/character/event-stat-change` | Apply a stat change from an event |
| `/api/character/cross-career-roll` | Roll on another career's skill table |
| `/api/character/ban-career` | Permanently ban a career |
| `/api/character/associate` | Add an ally, contact, rival, or enemy |
| `/api/character/end-term` | Close term; trigger aging; update pension |
| `/api/character/resolve-aging` | Apply player-chosen physical stat reductions |
| `/api/character/muster-out` | Cash or benefit roll from mustering-out table |
| `/api/character/muster-benefit-choice` | Resolve a skill-choice benefit (e.g. Advocate 1 or Broker 1) |
| `/api/character/anagathics/interest` | Set one-time anagathics preference |
| `/api/character/anagathics/attempt` | Roll SOC 10+ to start/continue anagathics |
| `/api/character/anagathics/stop` | Stop anagathics; trigger immediate aging roll |
| `/api/character/injury` | Roll on the injury table |
| `/api/character/injury-choice` | Player chooses which stat absorbs injury damage |
| `/api/character/home-forces` | Enrol in or resign from Home Forces Reserves |
| `/api/character/solsec-monitor` | Toggle SolSec Monitor status |

### Life events & psionics (POST)

| Endpoint | Returns |
|---|---|
| `/api/character/life-event` | Roll and resolve the life event sub-table |
| `/api/character/life-event-choice` | Resolve an interactive life event choice |
| `/api/character/psionics/test` | Roll PSI test |
| `/api/character/psionics/train` | Train a psionic talent |

### Utility

| Endpoint | Purpose |
|---|---|
| `/api/character/boon` | Use one boon re-roll |
| `/api/character/boon-pool` | Set the boon pool size (GM) |
| `/api/character/capsule` | Generate career narrative |
| `/api/character/connection` | Record a character connection |
| `/api/character/export-pdf` | Export character sheet as PDF |
| `/api/reload-rules` | Flush JSON caches without restart |
| `/api/health` | Sanity check |

---

## Character state

The `Character` object is the single source of truth. It lives in `localStorage`, travels with every API call, and is returned updated.

| Field | Purpose |
|---|---|
| `phase` | Current creation phase (`characteristics` → `society` → `species` → `background` → `pre_career` → `career` → `mustering` → `skill_package` → `done`) |
| `society_id` | Chosen polity; gates career lists, draft table, parallel service options |
| `species_id` | Resolved species (after Heritage Roll for Solomani) |
| `homeworld` / `homeworld_uwp` | Free-text homeworld name and UWP; shown in narrative and mission log |
| `extra_characteristics` | Optional rolled stats (PSI, WLT, LCK, MRL, STY, TER) if the player chose to add them |
| `psi` | PSI characteristic value; set by optional test or automatically for Zhodani |
| `pre_career_status` | Transient state during pre-career enrollment |
| `pre_career_permanent_dms` | Permanent DMs granted by pre-career education |
| `current_term` | In-progress career term (includes `cover_career_id` for SolSec Secret Agent; `frozen_watch` for cryo terms) |
| `term_history` | Every completed term with skills gained, events, survival, advancement |
| `completed_careers` | Summary record per career, including `benefit_rolls_earned` and `benefit_rolls_used` |
| `pending_benefit_rolls` | Rolls remaining in the muster-out phase |
| `pending_muster_benefit_choice` | Set when a muster-out benefit requires a skill pick (e.g. "Advocate 1 or Broker 1") |
| `pension_per_year` | Annual pension in Credits |
| `medical_debt` | Outstanding injury/anagathics debt; auto-deducted from cash rolls |
| `anagathics_interest` | `null` = not yet asked · `"yes"` = prompt each term · `"no"` = never |
| `anagathics_active` | Whether the character is currently using anagathics |
| `anagathics_terms_used` | Terms on anagathics; used as the positive aging DM |
| `home_forces_enrolled` | Whether the character is in the Home Forces Reserves |
| `solsec_monitor` | Whether the character is an active SolSec Monitor |
| `pending_life_event_choice` | Populated when a life event needs player input |
| `pending_injury_choice` | Populated when the player must choose which stat absorbs injury |
| `pending_career_mishap_choice` | Populated when a mishap requires player input |
| `forced_next_career_id` | Set by events/education that mandate a specific next career |
| `pending_transfer_career_id` | Career transfer offer from an event |
| `banned_career_ids` | Careers permanently closed |
| `career_package_id` | ID of the chosen career package, if one was taken instead of the normal career loop |
| `career_package_taken` | `true` once a career package has been applied; prevents any further careers |
| `good_fortune_benefit_dm` | DM tokens from Life Event 10, usable on benefit rolls |
| `gender` | Character gender (`"male"` / `"female"` / `null`); required for Aslan to gate career access by role |
| `clan_shares` | Aslan equivalent of Ship Shares; accumulated at mustering out (Hierate and Glorious Empire only) |
| `aslan_setup_status` | Tracks the Aslan background setup phases: clan type, ancestral deeds DM, territory type, family position, and rite score |
| `kkree_wives` | Number of wives in the K'kree patriarch's family group |
| `kkree_family_members` | List of family role entries |
| `kkree_soc_rank_degree` | K'kree social caste: `"servant_of_rankholder"` / `"kinsman_of_rankholder"` / `"rankholder"` |
| `kkree_specialist_area` | K'kree specialist area rolled at career start |

---

## Legal

*Traveller* is a trademark of Far Future Enterprises, used under licence by Mongoose Publishing. Rules referenced here are drawn from Mongoose Traveller 2e Core Rulebook, the Solomani Rim sourcebook, Aliens of Charted Space Volumes 1 and 5, The Glorious Empire sourcebook, and Pirates of Drinax. This project is a fan tool for personal use at the table. Rules text in the JSON data files is paraphrased under fair use for game-aid purposes — please own the rulebooks.
