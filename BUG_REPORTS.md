# Bug Reports

## Fixed Bugs

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

