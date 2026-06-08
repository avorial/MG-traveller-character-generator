# Bug Reports

## Fixed Bugs

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

