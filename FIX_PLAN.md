# Comprehensive Career Audit - Fix Plan

## Summary
- **Total Issues**: 94
- **CRITICAL**: 8 (missing entries)
- **MEDIUM**: 86 (text-to-effect mismatches)

## CRITICAL ISSUES (must fix immediately)

### 1. Droyne Event 7 (6 careers) - MISSING FROM _EVENT_EFFECTS
All Droyne careers have event 7 missing:
- droyne_drone
- droyne_leader
- droyne_sport
- droyne_technician
- droyne_warrior
- droyne_worker

**Action**: Add event 7 entries to `_EVENT_EFFECTS["droyne_*"]` dicts in lifepath.py
- All event 7s are narrative (no special effects)
- Should be: `7: []` (empty array)

### 2. Imperial Guard - NO _MISHAP_EFFECTS ENTRY
Career has 6 mishaps but no _MISHAP_EFFECTS dictionary entry

**Action**: Add complete _MISHAP_EFFECTS["imperial_guard"] section in lifepath.py

### 3. INI - NO _MISHAP_EFFECTS ENTRY  
Career has 6 mishaps but no _MISHAP_EFFECTS dictionary entry

**Action**: Add complete _MISHAP_EFFECTS["ini"] section in lifepath.py

## MEDIUM ISSUES (should fix)

### Group 1: Event 2 "Disaster" (40+ careers)
Text: "Disaster! Roll on the Mishap Table, but you are not ejected"
**Missing**: career_continues effect in on_pass

Affected careers:
- agent, army, aslan_ceremonial, aslan_envoy, aslan_management, aslan_military, aslan_military_officer
- aslan_outcast, aslan_scientist, aslan_space_officer, aslan_spacer, aslan_wanderer
- believer, citizen, confederation_army, confederation_navy, dolphin_civilian, dolphin_military
- drifter, entertainer, ge_fleet, ge_fleet_officer, ge_landless_one, ge_slave, ge_warrior, ge_warrior_officer
- girug_kagh_translator, hiver_academic, hiver_generalist, hiver_manipulator, hiver_merchant
- kkree_merchant, kkree_noble, kkree_pastoral, kkree_servant
- marine, merchant, navy, noble, party, philosopher_elder, prisoner, psion, rogue, scholar, scout
- solomani_marine, solsec, spirit_singer
- storm_knight_inconstant_star, storm_knight_shadows, storm_knight_thunder
- truther, vargr_army, vargr_citizen, vargr_corsair, vargr_emissary, vargr_law_enforcement
- vargr_loner, vargr_marines, vargr_merchant, vargr_navy, vargr_psion, vargr_scientist
- zhodani_agent, zhodani_army, zhodani_entertainer, zhodani_government, zhodani_guard
- zhodani_merchant, zhodani_navy, zhodani_scholar

**Fix**: All event 2s with trigger_disaster_mishap need `{"type": "career_continues"}` in the effect list

### Group 2: Event 10 Duel (Aslan military careers - 4 events)
Text: "Challenged to duel... lose SOC/Benefits"
**Missing**: forfeit_all_benefits when refusing duel

Affected:
- aslan_military_officer event 10
- aslan_space_officer event 10
- ge_warrior_officer event 10
- ge_fleet_officer event 10

**Fix**: Add `{"type": "forfeit_all_benefits"}` to on_fail effects

### Group 3: Various Mishaps with "not ejected" text
Several mishaps say "not ejected" but lack career_continues effect

Affected:
- aslan_spacer mishap 5
- confederation_navy mishap 2
- ge_fleet mishap 3
- Various others

**Fix**: Add `{"type": "career_continues"}` to effect lists

### Group 4: Other "lose all benefits" text
- aslan_outcast mishap 2
- believer event 9
- Various others

**Fix**: Add `{"type": "forfeit_all_benefits"}` to effect lists

## Implementation Order
1. Add Droyne event 7 entries (6 changes)
2. Add Imperial Guard _MISHAP_EFFECTS (1 large section)
3. Add INI _MISHAP_EFFECTS (1 large section)
4. Fix Event 2s with career_continues (40+ changes)
5. Fix Event 10 duels with forfeit_all_benefits (4 changes)
6. Fix remaining mishaps with not ejected → career_continues
7. Fix remaining "lose all benefits" → forfeit_all_benefits

## Files to Modify
- app/engine/lifepath.py (all changes)

## Testing
After fixes, run:
```bash
python audit_events_mishaps.py
```

Should show "0 total issues" or at least significant reduction in CRITICAL issues.
