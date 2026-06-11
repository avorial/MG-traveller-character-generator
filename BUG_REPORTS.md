# Bug Reports

## Fixed Bugs

### v30.69: Advancement "too long in this career" rule — off-by-one boundary
**Report:** "If your advancement roll is equal to or less than the number of terms you have spent in this career, then you cannot continue in this career after this term."

**Finding:** The rule *was* implemented (`advancement_roll` in `lifepath.py`), but with a strict `<` comparison (`r.total < term.term_number`) instead of RAW's "equal to or less than" (`<=`). This let a character who rolled *exactly* their terms-served stay in the career when they should have been forced out at end of term. `term.term_number` already correctly counts terms served **in the current career** (resets to 1 on a new career, line 6232), so the baseline was right — only the boundary was wrong.

**Fix:** Changed the comparison to `r.total <= term.term_number` and corrected the log wording to "equal to or less than terms served". Noble auto-advance remains exempt (its roll always counts). `forced_from_career` flows downstream unchanged.

**Verification:** Boundary unit-tested directly — roll total 2 with 2 terms served now forces out (was: stayed); total 3 still continues. All 660 tests pass.

---

### v30.68: ✨ AI Story — Bring Your Own AI for Narrative Prose (feature)
**Request:** Let players plug in their own AI to turn the factual career narrative into an actual story.

**Implementation:**
- **`app/engine/ai_narrative.py`** — builds a strict prompt from the v30.67 template capsule (the fact sheet: "stay faithful to the facts, don't invent events/ranks/names, no game mechanics, 400–600 words, chosen tone") and calls one of two providers:
  - **Claude** via the official `anthropic` SDK (default `claude-opus-4-8`, adaptive thinking, optional base-URL override for proxies); typed errors map to friendly 401/403/404/429/502 messages.
  - **OpenAI-compatible** via httpx → `{base_url}/chat/completions` — covers Ollama, LM Studio, OpenRouter, OpenAI, LiteLLM. Key optional (local models), generous 300s timeout, Docker `host.docker.internal` hint on connection failure.
- **`app/main.py`** — `POST /api/character/ai-narrative` (provider, api_key, model, base_url, tone). The key is passed through per-request and **never stored server-side**.
- **`app/static/js/app.js`** — Career Narrative card gains **✨ AI STORY** and **⚙ AI SETTINGS** (provider / key / model / base URL / tone, persisted in `localStorage` only). Unconfigured click opens settings. The story replaces the capsule, persists to `capsule_description`, and therefore flows into the Foundry actor bio and PDF; REGENERATE still restores the template rundown.
- `requirements.txt` — added `anthropic` (brings httpx).

**Verification:** Both provider paths exercised offline against mock servers through the real endpoint (adaptive thinking + default model asserted on the Claude path; markdown-fence stripping; 401/400/502/timeout error mapping). Live browser end-to-end: configure OpenAI-compatible → ✨ AI STORY → 3-paragraph story renders in the capsule box and persists to the character. All 660 tests pass.

---

### v30.67: Generate Narrative Produces Actual Prose (feature)
**Request:** The career narrative dumped raw rulebook/log text — dice mechanics ("Roll Investigate 8+… If you succeed, gain REP +1 and DM+1…"), second person, "Gained Contact: Unnamed Contact" repeated six times, and "Basic training: Electronics (Comms) 0, Basic training: Drive 0…" prefixes.

**Implementation (`app/engine/lifepath.py` `generate_capsule` + helpers):**
- **Mechanics stripped:** sentences containing roll/DM/dice/choice instructions are dropped (`_CAPSULE_MECH_RE`), with a fallback that keeps the narrative lead of an event cut at the first mechanics marker.
- **Third person:** "You develop a network…" → "They develop a network…" (`you/your/yourself` → `they/their/themselves`; identical verb forms make this safe).
- **Associates summarised:** per-term "Gained Contact: Unnamed Contact" spam becomes "The term left them with three contacts" — named ones are listed ("an enemy (Corrupt Politician)").
- **Training reads as a sentence:** prefixes stripped ("Basic training:", "Rank bonus:", "Gained", "Increased X to N"), deduped, with rotating openers; basic-training terms get "Basic training grounded them in …".
- **Promotions called out:** rank increases vs the previous term in the same career render as ", newly promoted to Captain" instead of "serving as a Captain".
- **Mishaps narrated:** "The term ended badly: they accept a contract that goes against their moral code…" (mechanics tail removed).
- **Richer opening/closing:** characteristic-driven adjectives ("sharp-minded, highly educated"), a retirement-rank sentence ("They left the SolSec as a Colonel."), and a closing grudge line ("Not everyone remembers them fondly — an enemy and a rival still hold a grudge, the Corrupt Politician chief among them.") or a well-liked line for ally-heavy characters.
- Career-package logs cleaned too ("Took the X career package" bookkeeping skipped; "Gained/Already has/Increased … to N" verbs normalised).

The capsule persists to `capsule_description`, so the improved prose flows into the Foundry export's actor bio and the PDF.

**Verification:** Emma-style fixture (SolSec, 3 terms, mishap, contact spam) and two random `generate_npc()` characters (incl. career packages) all render as clean prose; all 660 tests pass.

---

### v30.66: Finish-Stage Pre-Flight — Benefit Choices, Unnamed Associates, Lean Export (features)
**Request:** Before export, the finish screen should resolve leftover loose ends: (2) "X or Y" benefit choices stored as a single equipment string, (3) placeholder associates ("Unnamed Contact", "From mustering out"), and (4) an option to skip the embedded source character for a lean VTT-only Foundry file.

**Implementation:**
- **Benefit choices** — `lifepath.resolve_equipment_choice(index, chosen)` (+ `POST /api/character/resolve-equipment-choice`): validates the pick against the options split from the item name, removes the item, and applies the pick via `_apply_benefit` (so ship shares, implants, weapons, associates, skills all land correctly). Done screen shows an "⚖ Unresolved Benefit Choices (N)" card with one button per option.
- **Unnamed associates** — "👥 Unnamed Associates (N)" card with per-row input + 🎲 (reusing the D66 personage + species-name generator and the `op:"update"` associate endpoint) plus a **🎲 GENERATE ALL** button. Detection: empty / "unnamed" / "from mustering out" descriptions.
- **Lean export** — `character_to_foundry(include_source=False)` omits the `flags.tvgen` embed; `export-foundry` accepts `include_source` (default true); a checkbox under the export buttons controls it.

**Verification (live browser):** "Combat Implant or two Ship Shares" → two Ship Shares (ship_shares 0→2, item removed); "Rifle or Carbine" → Rifle in equipment; cards disappear when cleared. GENERATE ALL named both placeholders, left the real Ally untouched. Full export carries `flags.tvgen` (20.7KB), lean doesn't (15.8KB); checkbox drives the flag. All 660 tests pass.

---

### v30.65: Foundry Export — Full MGT2E Skill Structure (label/combat/default) for Weapon Dropdowns
**Request:** Foundry exports (Travellers, NPCs, **and robots**) must use the full MGT2E skill-speciality structure. Combat-skill specialities were missing `label` / `combat` / `default`, which breaks weapon-skill selection in Foundry.

**Implementation:**
- **`app/engine/foundry_export.py`** (biological + NPC): combat skills (Gun Combat, Melee, Heavy Weapons, Gunner) now always emit all core specialities, each with `id, label, combat:true, default, trained, value`; the parent carries `default`. Untrained = `value "0"` + `trained:false`; trained = level as a string (supersedes the v30.58 `-3` value). A trained speciality marks its parent trained at 0 (RAW). Non-combat specialities get `label`+`default` (no `combat`). Added `_COMBAT_SKILLS` and `_SKILL_DEFAULT_CHAR` (Gun Combat/Melee/Heavy Weapons → DEX, Gunner → INT, etc.).
- **`app/static/js/app.js`** `createRobotFoundryExport`: rebuilt robot skills with the identical structure (same maps/labels/defaults) so robots are not simplified.

**Verification:** Gun Combat (Energy) 2 exports as `guncombat` parent `trained:true value "0" default DEX` with energy `{label:"Energy", combat:true, default:"DEX", trained:true, value:"2"}` and slug/archaic present untrained; identical output from the robot path; round-trip import still drops untrained entries (no noise). All 660 tests pass.

---

### v30.64: Solomani Qualification-Failure Draft Used the Imperial Table
**Symptom:** A Solomani Confederation character who failed a career qualification and accepted the draft was drafted into **Imperial** services (Navy / Army / Marine / Scout / Agent) instead of Confederation ones.

**Root Cause:** `draft_into_service()` (the general qualification-failure draft) branched for Vargr Extents and Zhodani Consulate but had **no Solomani branch**, so it fell through to the generic Imperial `_DRAFT_TABLE`. (The pre-career education-event-11 draft already had a Solomani table; the qualification-failure path didn't.)

**Fix (`app/engine/lifepath.py`):** Added `_SOLOMANI_DRAFT_TABLE` and a `solomani_confederation` branch, mirroring the event-11 Solomani draft: 1 Confederation Navy (Line/Crew), 2 Confederation Army (Infantry), 3 Solomani Star Marines (Star Marine), 4 Merchant (Merchant Marine), 5 SolSec (Field Agent), 6 Agent (Law Enforcement).

**Verification:** All six entries resolve to valid careers/assignments; a Solomani accepting the draft now lands in Confederation Navy. All 660 tests pass.

---

### v30.63: Full-Page Sheet Colour Buttons Didn't Work
**Symptom:** On the standalone "⛶ FULL SCREEN" character sheet, the COLOUR buttons (Amber / Green / B&W Print / Dark Print) did nothing.

**Root Cause (two):**
1. The standalone window freezes the sheet's interactive controls with `button, input { pointer-events: none }` — which also disabled the colour/print **toolbar** buttons, so clicks never registered.
2. The GREEN button applied `gm-active` (the GM-panel class), not an actual theme.

**Fix (`app/static/js/app.js`, `openTASFullscreen`):**
- Added `#sheet-toolbar button { pointer-events: auto !important; opacity: 1 !important; cursor: pointer; }` so the toolbar stays clickable while the rest of the sheet stays inert.
- GREEN now applies `theme-light` (the real green theme, loaded via the page's stylesheets), and the script's theme-reset list was updated to match.

**Verification:** Generated standalone HTML now carries the pointer-events override and the corrected theme classes; JS parses; all 660 tests pass (no engine change).

---

### v30.62: Cascade Cleanup Rejected Valid Profession/Language Specialties
**Symptom:** Cleaning up a Profession (or Language) cascade skill at completion errored with e.g. `'Hostile Environment/High-g' is not a valid Profession speciality.`

**Root Cause:** The cleanup picker offers specialties from the frontend `CASCADE_SKILLS` map, but the backend validated the choice against `skills.json` — and the two lists differ (Profession entirely; Language partly: Bilanidin/Trokh). Also, the picker's Profession names were non-canonical/odd.

**Fix:**
- `app/engine/lifepath.py` `cleanup_cascade_specialties()`: still requires the parent to be a cascade skill, but **trusts the player's chosen specialty** from the curated picker instead of hard-rejecting names not in `skills.json` (fixes Profession and Language).
- `app/static/js/app.js` `CASCADE_SKILLS.Profession`: replaced the odd names (`Hostile Environment/High-g`, `Colonist/Farming`, …) with the canonical `skills.json` list (Belter, Biologicals, Civil Engineering, Construction, Hydroponics, K'kree Ritual, Miner, Polymers, Religion).

**Verification:** Cleanup with `Profession → Belter` applies (`Profession (Belter) 2`, parent → 0); the legacy name no longer errors; a non-cascade skill is still rejected. All 660 tests pass.

---

### v30.61: Characteristic DM Extends Above 15 (High & Low Characteristics)
**Request:** Characteristics above 15 (some species cap at 17–18) should follow the extended Characteristic Modifiers table — 15-17 → +3, 18-20 → +4, 21-23 → +5, +1 per +3 thereafter — instead of capping the DM at +3.

**Fix:** Replaced the capped DM ladders with the closed form `(score // 3) - 2` (0 stays the special case at -3), which reproduces the whole table including the extension, in all three implementations:
- `app/engine/dice.py` `characteristic_dm()` (used everywhere via `_char_dm`, incl. REP/PSI/RES/TER/FOL)
- `app/static/js/app.js` `charDM()` (sheet, rolls, DM displays)
- `app/engine/pdf_sheet.py` `char_dm()` (PDF export)

**Verification:** New test assertions: 15→+3, 17→+3, 18→+4, 20→+4, 21→+5, 23→+5, 24→+6. All 660 tests pass.

---

### v30.60: Foundry Import — Muster Benefit Associates Come In As Associates
**Request:** Muster-out benefits should import too. (Most already did — cash, pension, ship shares, medical debt via finance; gear via equipment items; benefit contacts/allies via associate items.) The wart: a muster-benefit associate exported as an equipment item (e.g. **"a Contact"**, "an Ally") imported as a piece of *gear* named "a Contact".

**Fix (`app/engine/foundry_export.py`):** In the item loop, an equipment item whose name is an associate type ("a Contact" / "an Ally" / "Rival" / "Enemy") is now added as an Associate (`[From mustering out]`) instead of equipment.

**Verification:** Emma Colbert (fully-updated) → the "a Contact" muster item now lands in Associates (18 contacts) and the equipment list holds only real gear (SC Courier ×3, Combat Implant choice); pension Cr10,000, etc. still import. All 660 tests pass.

---

### v30.59: Foundry Import Reconstructs Career History from Term Items
**Request:** Importing a third-party Foundry actor brought in contacts/equipment but not careers — even though the Foundry `term` items carry the career/assignment/rank (Foundry itself shows them as a Career Terms list).

**Implementation (`app/engine/foundry_export.py`):** `foundry_to_character()` now reconstructs `term_history` + `completed_careers` from the `term` items. Each term's `system.term.assignment` ("Career: Assignment (Rank Title)") is parsed and mapped: career name → career_id, assignment name → assignment_id, rank title → rank number (via the career's rank table). Consecutive same-career terms are grouped into one `CareerRecord` with terms_served, final_rank/title, and benefit_rolls_earned (terms + rank bonus). Per-term rolls/benefit counts aren't in a Foundry export, so those remain approximate.

**Verification:** Both supplied Emma Colbert actors → `solsec / secret_agent`, 5 terms, rank 5 (Colonel); a synthetic Darren Cogs (Scholar/Physician) → 7 terms, rank 6 (Dean) with per-term ranks (Researcher 1, Scientist 3, Professor 5, Dean 6). Contacts and equipment still import. All 660 tests pass.

---

### v30.58: Foundry Export Writes Untrained Skills as -3 (MGT2e convention)
**Request:** Our Foundry export wrote untrained skills as value `0`; the current Foundry MGT2e convention (and real-world actors) use `-3`. Re-exporting an older character should produce the full skill tree with untrained skills at `-3`.

**Fix (`app/engine/foundry_export.py`):** In the skills builder, trained skills/specialties keep their level as a string (`"0"/"1"/"2"`), and untrained ones are now written as `-3` (with `trained:false`) so Foundry shows the −3 unskilled DM instead of a misleading 0.

**Verification:** Export of a sample character shows trained skills (`admin "0"`, `guncombat "1"`, `carouse "2"`) and untrained skills (`astrogation/broker/melee/stealth = -3`); untrained specialties are `-3` while a trained `Pilot (Small Craft) 0` is kept. Round-trip import still drops all `-3` entries (no negative-level skills created). All 660 tests pass.

---

### v30.57: Foundry Import — Keep Trained Specialties Whose Entry Omits "trained":true
**Symptom:** Real third-party Foundry actors (e.g. Emma Colbert) imported via v30.56 but lost trained specialties — Electronics (Computers) 1, Science (Psychology) 1, Pilot (Small Craft), etc. (Separately, an import "failing right away" on the live site is a deploy-lag symptom: pre-v30.56 builds have no Foundry support, so importing a Foundry JSON just breaks — the fix is to deploy the new build.)

**Root Cause:** Many Foundry exports mark only *untrained* specialties (`trained:false`, value `-3`) and omit `trained:true` on the trained ones. `foundry_to_character()` required `sp.get("trained")` truthy, so trained specialties were skipped.

**Fix (`app/engine/foundry_export.py`):** A specialty/skill is now treated as trained unless explicitly `trained:false`; entries with a negative (`-3`) placeholder value are skipped. Parent skills follow the same rule.

**Verification:** Both supplied Emma Colbert actors convert with full skills (Electronics (Computers) 1, Science (Psychology) 1, Pilot (Small Craft) 0, …), 17 associates, equipment, and pension — confirmed directly and via the live `importCharacter` flow (lands on the finish screen). All 660 tests pass.

---

### v30.56: Import Reads Both Native and FoundryVTT JSON (feature)
**Request:** Let IMPORT JSON read both normal (native) exports and FoundryVTT actor JSON.

**Implementation (two tiers):**
- **Tier A — lossless round-trip for our own exports.** `character_to_foundry()` now stashes the full native character in `flags.tvgen.character` (Foundry ignores unknown flag namespaces, so it's inert there). On import, that character is restored verbatim.
- **Tier B — best-effort import of third-party Foundry actors.** `foundry_to_character()` reverse-maps a Mongoose `traveller` actor: characteristics, skills (via inverse skill-id/spec-id tables, seeding cascade parents at 0), finance (credits/pension/debt/ship shares), bio (species via reverse name lookup, age, gender, homeworld), and `items[]` → associates + equipment. The result is a finished character (phase `done`); career history and the lifepath log are not reconstructed (a one-time alert says so).
- `app/main.py`: `POST /api/character/import-foundry` (+ `FoundryImportAction`).
- `app/static/js/app.js`: `importCharacter()` detects a Foundry actor (`type:"traveller"` + `system`, unwrapping `[actor]` / `{actor:…}` shapes), routes it through the endpoint, and keeps native JSON on the existing client path.

**Verification:** Round-trip (export→import) is lossless; a stripped (third-party) actor reconstructs characteristics, skills with specialties, credits/pension, species_id, associates and equipment — verified both directly and through the live `importCharacter` flow. All 660 tests pass.

---

### v30.55: Re-Import Finished Characters to Clean Them Up at the Finish Stage
**Request:** Be able to pull a finished character back into the generator and clean it up (cascade specialties, etc.) at the finish stage.

**Implementation (`app/static/js/app.js`):** `importCharacter()` now resets transient navigation/selection state (`subPhase`, `lastRoll`, `lastAdvanceRoll`, `cascadeCleanupMode`/choices, `selectedMusterIndex`, `selectedCareer`/assignment, `pendingCareerSpecialty`, `pendingAdvancementSkill`) before rendering. A re-imported finished character (phase `done`) now reliably lands on the "Your Traveller Is Ready" screen — where the v30.54 **CLEAN UP SPECIALTIES** card appears for any over-leveled cascade skills — instead of inheriting the previous view's state. Mid-creation saves still resume at the correct step via the career sub-phase inference. (The always-visible **IMPORT JSON** header button is how characters are pulled back in.)

**Verification:** With a deliberately dirty UI state (mid-cleanup, stale event sub-phase), importing a finished character resets the state and the done screen renders the cleanup card + "CLEAN UP SPECIALTIES (2)" for its invalid cascade skills (Gun Combat 3, Melee 1). All 660 tests pass.

---

### v30.54: Cascade Cleanup Button on the Final "Your Traveller Is Ready" Screen
**Status:** FIXED  
**Symptom:** v30.53 added the CLEAN UP SPECIALTIES button to the muster-out "All Benefits Claimed" screen (PHASE 05), but the actual finalized **done** screen (PHASE 06 — "Your Traveller Is Ready") had no button, so a completed character with over-leveled cascade skills (Gun Combat 1, Pilot 1, Melee 1) couldn't reach the cleanup there.

**Fix (`app/static/js/app.js`):** The done screen now shows a "🧹 Cascade Skills Need Specialties" card with a **CLEAN UP SPECIALTIES (N)** button when `invalidCascadeParents()` finds any, routes into `renderCascadeCleanup()` while `uiState.cascadeCleanupMode` is set, and wires the picker via a shared `wireCascadeCleanup()` (used by both the muster and done screens). The cleanup panel header is now neutral ("SKILL CLEANUP") since it appears in both contexts.

**Verification:** Live UI on the done screen — card shows "CLEAN UP SPECIALTIES (3)"; picker assigns Gun Combat (Slug) / Pilot (Small Craft) / Melee (Blade); apply converts all, preserves a pre-existing Pilot (Capital Ships) specialty, returns to the done screen with the card gone and 0 invalid remaining. All 660 tests pass.

---

### v30.53: Clean-Up Button for Over-Leveled Cascade Skills (feature)
**Request:** At character completion ("Your Traveller is ready"), add a button to fix cascade skills held above level 0 with no specialty (e.g. "Gun Combat 2", "Pilot 1") — letting the player choose which specialty each level moves into.

**Implementation:**
- `app/engine/lifepath.py`: `cleanup_cascade_specialties(character, {parent: speciality})` moves each over-leveled bare cascade parent's level into the chosen specialty and drops the parent to 0 (MgT 2e p.59). Validates against `rules.skill_specialities()`.
- `app/main.py`: `POST /api/character/cleanup-cascade-specialties`.
- `app/static/js/app.js`: the muster-out "All Benefits Claimed" screen now warns when cascade parents are over-leveled and shows a **🧹 CLEAN UP SPECIALTIES (N)** button. It opens a picker listing each offending skill with its specialty options; APPLY is gated until every one is assigned. (`invalidCascadeParents()` detects them via `CASCADE_SKILLS`.)

**Verification:** Engine test — Gun Combat 2 → Gun Combat (Slug) 2 + Gun Combat 0; Admin (non-cascade) untouched. Live UI end-to-end — button appears with count, picker assigns Slug/Small Craft, APPLY converts both and clears the warning. All 660 tests pass.

---

### v30.52: Name/Type Generator for Mustering-Out Contacts & Allies (feature)
**Request:** Allow associates gained at muster-out (Contact / Ally / D3 Contacts, etc.) to use the same type+name generator already available earlier in the generator (the D66 personage table + species-name generator used for career-event associates).

**Implementation:**
- `app/engine/lifepath.py`: `muster_out_roll()` now returns `new_associates` (index/kind/description of any associates the benefit added). Added `update_associate(character, index, description)` to rename an associate.
- `app/main.py`: `AssociateAction` / `/api/character/associate` gained an `op: "update"` (rename by index).
- `app/static/js/app.js`: the muster-out result screen lists each newly granted associate with an editable field + a **🎲 Generate** button that fills a D66 personage type + a species-appropriate name (reusing `_SOL_CONTACTS` + `generateSpeciesName`). Edits save automatically via the update op without re-rendering (inputs keep focus while naming several in a row).
- `app/static/css/style.css`: styling for the naming rows.

**Verification:** Backend returns `new_associates` for a Contact benefit; live UI — Generate fills "Alien Ambassador or Trade Delegate — Abraham Balde" and persists to the associate; manual typing also persists. All 660 tests pass.

---

### v30.51: Muster-Out Couldn't Roll Benefits for a Second Stint in the Same Career
**Status:** FIXED  
**Symptom:** A character who served the **same career twice** (e.g. two separate Bounty Hunter careers) could not claim the second stint's mustering-out rolls. Selecting the later Bounty Hunter card showed the *first* one's table ("0 of 1 rolls remaining"), and the ROLL CASH / ROLL BENEFIT buttons were disabled.

**Root Cause:** The muster-out flow identified careers by `career_id` on both ends:
- Frontend: `data-muster-career="${career_id}"`, and `careers.find(x => x.career_id === selected)` always returned the **first** record.
- Backend: `muster_out_roll()` did `next(c for c in completed_careers if c.career_id == career_id)` — same first-match collapse.

So two stints of the same career collapsed onto the first record; once it was exhausted, the second could never be rolled.

**Fix:** Identify careers by their **index** in `completed_careers`:
- `app/static/js/app.js`: cards key on `data-muster-career-index`; selection stores `uiState.selectedMusterIndex`; the table and roll handlers resolve the record via `completed_careers[index]` and send `career_index` to the API; selected card now highlights.
- `app/main.py` / `app/engine/lifepath.py`: `MusterOutAction` and `muster_out_roll()` accept an optional `career_index` and use it to locate the exact record (validated against `career_id`), falling back to first-match for backward compatibility.

**Verification:** Engine test — rolling with `career_index=2` claims the 3-term Bounty Hunter stint and leaves the exhausted 1-term stint untouched; the exhausted index still correctly errors. Live UI: selecting the second Bounty Hunter shows "3 of 3 rolls remaining" with enabled buttons; rolling decrements that stint only and spends one of the shared 7 benefit rolls. All 660 tests pass.

---

### v30.50: Solomani "Racial Incident" Life Event Locked the Character
**Status:** FIXED  
**Symptom:** A Solomani character who rolled the **Racial Incident** life event during a career term (pending_life_event_choice = {kind: "racial_incident"}) could not progress. Choosing Rival or Enemy did nothing / errored, and reloading the save dropped the player back at Basic Training with no way to reach the choice.

**Root Causes (two):**
1. **Backend gap (the actual lock):** `resolve_life_event_choice()` handled `romantic_split` and `betrayal_no_associates` but had **no `racial_incident` branch** — yet `apply_life_event()` produces exactly that kind for Solomani characters. Clicking Rival/Enemy hit `POST /api/character/life-event-choice` and got **400 "Unknown pending life event kind: 'racial_incident'"**, so the choice could never resolve.
2. **Resume routing:** the career-loop sub-phase is stored only in `uiState`, never in the saved character. On reload/import, `renderActiveTerm` defaulted `subPhase === null` to the **training** step, stranding the pending life event (and, if continued, re-rolling survival/event).

**Fix:**
- `app/engine/lifepath.py`: added a `racial_incident` branch to `resolve_life_event_choice()` (Rival/Enemy → add the matching associate), mirroring `romantic_split`.
- `app/static/js/app.js`: `renderActiveTerm` now calls `inferResumeSubPhase(term)` when `subPhase === null`, routing to the correct step (event/mishap/advance/decide) based on term state and pending choices, and reconstructing the minimal event `lastRoll` so the pending picker renders on resume.

**Verification:** Audited all life-event kinds set vs. handled — `racial_incident` was the only genuine gap. Live end-to-end with the user's save: character resumes at the event step with the Rival/Enemy picker (advancement gated), choosing Rival adds "Rival [Racial Incident]", clears the pending choice, and enables ATTEMPT ADVANCEMENT. Backend resolve verified directly; all 660 tests pass.

---

### v30.48: Advancement Bonus Skill — Cascade Specialty Picker Never Appeared
**Status:** FIXED  
**Symptom:** On a successful advancement, the promotion's bonus skill roll could land on a cascade skill (e.g. Melee). The result screen showed "BONUS SKILL GAINED — Melee speciality choice pending", but **no specialty picker ever appeared**, so the player couldn't choose Blade/Bludgeon/Natural/Unarmed and the skill was left unresolved.

**Root Cause:** `skill_roll()` correctly stashed the cascade prompt in `pending_career_event_choice` and returned "… speciality choice pending", but the frontend's **advancement** skill-table handler (unlike the normal training handler) never set `uiState.pendingCareerSpecialty`, and the advancement result view had no specialty-picker UI. The pending choice was orphaned. Additionally, `/api/character/apply-specialty` never cleared `pending_career_event_choice`, so a resolved cascade could leak a stale skill picker into a later event.

**Fix:**
- `app/static/js/app.js`: the advancement bonus-skill handler now detects a bare cascade result and sets `uiState.pendingCareerSpecialty` (mirroring the training-phase flow); the advancement result view renders the existing "CHOOSE SPECIALTY" picker and **gates the Another-Term / Muster-Out buttons** until a specialty is chosen; the specialty-pick handler syncs `advancementSkillGained` so the resolved skill (e.g. "+1 Melee (Blade) (level 1)") displays.
- `app/main.py`: `/api/character/apply-specialty` now clears `pending_career_event_choice` after applying, preventing the stale-picker leak (also benefits the normal training cascade flow).

**Verification:** Live-preview end-to-end — promotion → bonus skill Melee → picker shows (Blade/Bludgeon/Natural/Unarmed) with term-decision buttons gated → choosing Blade applies "Melee (Blade) 1", reveals the decision buttons, updates the bonus-skill text, and clears the backend pending choice. All 660 tests pass.

---

### v30.47: Bounty Hunter Event 9 — Skill Check Resolved Twice (real root cause)
**Status:** FIXED  
**Symptom:** Bounty Hunter event 9 ("Roll Investigate 8+ or Streetwise 8+...") presented **two** skill pickers and let the player roll the check twice with conflicting outcomes. A user screenshot showed both branches applying at once: a "Failure" block (Streetwise rolled 4 → mishap + Enemy) **and** an "Auto-applied" block (Streetwise rolled 8 → PASS → REP+1, DM+1 Benefit), plus a stray "+ Add Enemy" associate op.

**Root Cause:** The frontend has **two** independent event skill-check systems that both reacted to the same event text:
1. The backend's authoritative structured `pending_event_choice` skill_check (proper on_pass/on_fail applied server-side).
2. A frontend text-parser (`parseEventContestedRoll`) that scrapes "Roll <Skill> N+" from the event text and renders its own picker (`eventContestedResolved`), resolving client-side.

Both rendered, so the player rolled the check twice. Separately, a third text-parser (`parseEventAssociateOps`) scraped "gain an Enemy" and offered a manual "+ Add Enemy" op, duplicating the skill_check's on_fail enemy. (The earlier v30.45 dm_grants fix addressed only one symptom — the stray DM+1 button — not the double roll.)

**Fix (`app/static/js/app.js`):**
- Gate the text-parsed contested roll on `!lr.pendingEventChoice` — when the backend supplies a structured skill_check, it is authoritative and the text-parsed picker stands down. Events that legitimately rely on the text-parser (navy[3], drifter[6], scholar[9], …) have no `pending_event_choice`, so they are unaffected.
- Extend `suppressAssocOps` to fire for **any** `pending_event_choice` (was only `pending_choice`), and guard the auto-add-ally block with the same flag, so structured effects own all associates and the text-parsed associate picker/auto-add cannot duplicate them.

**Verification:** Live-preview render test confirms event 9 now shows exactly one skill picker, no contested picker, and no stray associate op; a control event with no structured choice still renders its contested picker. All 660 tests pass.

---

### v30.44: Background Skills Duplicate Specialty + Parent Skill
**Status:** FIXED  
**Symptom:** When selecting a background skill with a specialty (e.g., "Science (Xenology)"), the character would end up with both:
- Science 0
- Science (Xenology) 0

**Root Cause:** In `character.py`, the `add_skill()` method was auto-seeding the parent skill whenever ANY speciality was added, including at level 0 (background training).

**Fix:** Modified condition at line 471 from `if speciality:` to `if speciality and new_level > 0:` to only auto-seed parent skills at level 1+.

**Rationale:** Background training (level 0) should only grant the chosen specialty, not the parent skill. The auto-seed at level 1+ prevents duplicate entries when a later career table adds the same skill.

---

### v30.45: Bounty Hunter Event 9 — Stray DM+1 Benefit Reward ("double prompt")
**Status:** FIXED  
**Symptom:** Bounty Hunter event 9 ("...gain REP +1 and DM+1 to one Benefit roll. If you fail, roll on the Mishaps table and gain an Enemy.") presented what looked like a second prompt alongside the Investigate/Streetwise skill check, and the player could end up with **DM+1 to their next Benefit roll even when the skill check FAILED**. (Confirmed via user save: `dm_next_benefit: 1` + log "Event DM chosen: DM+1 to next Benefit roll" despite "Mishap skill check (Investigate): 7 vs 8+ — fail".)

**Root Cause:** Two systems reacted to the same event text:
1. The backend `skill_check` pending choice, whose `on_pass` correctly grants `dm_benefit +1` **only on a pass**.
2. `_parse_event_dms()` independently scraped "DM+1 to one Benefit roll" into `dm_grants`, which the UI could surface as a **separately claimable** reward — decoupled from the skill check.

**Fix:** In `event_roll()` (`app/engine/lifepath.py`), when the event creates a `pending_career_event_choice`, drop all *unapplied* (conditional) text-parsed `dm_grants`. The conditional reward is owned by the skill_check's `on_pass`/`on_fail` and must never be grantable independently. (The frontend already display-gated these on `!lr.pendingEventChoice` since v24.11; this is the authoritative backend guard so the wrong reward can never be applied regardless of render path.)

**Rationale:** Verified the filter keeps `applied:True` (unconditional) grants intact, so events that legitimately auto-apply a DM plus offer a separate choice are unaffected.

---

## Known Bugs (Pending Fix)

### (Historical) Bounty Hunter Event 9: Double Skill Choice Prompt — superseded by v30.45 fix above
**Status:** FIXED (see v30.45)  
**Symptom:** Bounty Hunter event 9 triggers a skill check "Investigate 8+ or Streetwise 8+". The player sees a choice prompt to select which skill to roll, and this choice appears TWICE in the UI.

**Career:** bounty_hunter  
**Event:** 9  
**Effect Entry:** Lines 1068-1074 in `app/engine/lifepath.py` (_EVENT_EFFECTS section)
```json
{
  "type": "skill_check",
  "skills": [{"name": "Investigate"}, {"name": "Streetwise"}],
  "target": 8,
  "on_pass": [{"type": "dm_benefit", "amount": 1}],
  "on_fail": [{"type": "trigger_disaster_mishap"}, {"type": "enemy", "desc": "Enemy [Corrupt Politician]"}]
}
```

**Suspected Cause:** The skill choice prompt rendering code (app.js, lines 9831-9844) may be:
1. Being invoked twice by event loop/re-render
2. Having click handlers attached twice
3. An issue with how the pending_career_mishap_choice state is being managed

**Investigation Points:**
- Frontend skill_choice rendering at app.js lines 9831-9844
- Click handler wiring for `.event-choice-skillcheck` buttons
- Possible double-render in the event resolution phase

**Fix Approach:** Need to trace when the pending choice is rendered and ensure it's only shown once. May require:
- Check if skill_check with multiple skills inadvertently triggers a secondary choice creation
- Verify click handlers are wired only once per render
- Confirm `lr.eventChoiceResolved` flag is being set correctly after first choice

---

## Testing Checklist

When fixes are complete, verify:

- [ ] Background skill with specialty (e.g., Science (Xenology)) appears only once at level 0
- [ ] Background skill choice shows no duplicate parent skill entries
- [ ] Bounty Hunter event 9 shows skill choice prompt only once
- [ ] Selecting either Investigate or Streetwise in event 9 works without double-prompting
- [ ] Other multi-skill checks don't have the same double-prompt issue

