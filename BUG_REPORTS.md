# Bug Reports

## Fixed Bugs

### v30.44: Background Skills Duplicate Specialty + Parent Skill
**Status:** FIXED  
**Symptom:** When selecting a background skill with a specialty (e.g., "Science (Xenology)"), the character would end up with both:
- Science 0
- Science (Xenology) 0

**Root Cause:** In `character.py`, the `add_skill()` method was auto-seeding the parent skill whenever ANY speciality was added, including at level 0 (background training).

**Fix:** Modified condition at line 471 from `if speciality:` to `if speciality and new_level > 0:` to only auto-seed parent skills at level 1+.

**Rationale:** Background training (level 0) should only grant the chosen specialty, not the parent skill. The auto-seed at level 1+ prevents duplicate entries when a later career table adds the same skill.

---

## Known Bugs (Pending Fix)

### Bounty Hunter Event 9: Double Skill Choice Prompt
**Status:** INVESTIGATING  
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

