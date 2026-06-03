#!/usr/bin/env python3
"""
Fix all 86 MEDIUM issues in lifepath.py.

The main issues are:
1. Event 2 "Disaster" entries missing career_continues effect
2. Some event 10 duel choices missing forfeit_all_benefits
3. Various mishaps/events with "not ejected" text missing career_continues
4. Some "lose all benefits" text missing forfeit_all_benefits

Strategy: Read the file, find _EVENT_EFFECTS and _MISHAP_EFFECTS, and patch them.
"""

import json
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "app"))
from engine import lifepath

# Mapping of career -> event numbers that need career_continues added
event2_needs_cc = {
    "agent": [2],
    "army": [2],
    "aslan_ceremonial": [2],
    "aslan_envoy": [2],
    "aslan_management": [2],
    "aslan_military": [2],
    "aslan_military_officer": [2, 10],
    "aslan_outcast": [2],
    "aslan_scientist": [2],
    "aslan_space_officer": [2, 10],
    "aslan_spacer": [2],
    "aslan_wanderer": [2],
    "believer": [2, 9],
    "citizen": [2],
    "confederation_army": [2],
    "confederation_navy": [2],
    "dolphin_civilian": [2],
    "dolphin_military": [2],
    "drifter": [2, 6],
    "entertainer": [2],
    "ge_fleet": [2],
    "ge_fleet_officer": [2, 10],
    "ge_landless_one": [2],
    "ge_slave": [2],
    "ge_warrior": [2],
    "ge_warrior_officer": [2, 10],
    "girug_kagh_translator": [2],
    "hiver_academic": [2],
    "hiver_generalist": [2],
    "hiver_manipulator": [2],
    "hiver_merchant": [2],
    "kkree_merchant": [2],
    "kkree_noble": [2],
    "kkree_pastoral": [2],
    "kkree_servant": [2],
    "marine": [2],
    "merchant": [2],
    "navy": [2],
    "noble": [2],
    "party": [2],
    "philosopher_elder": [2],
    "prisoner": [2],
    "psion": [2],
    "rogue": [2, 8],
    "scholar": [2],
    "scout": [2],
    "solomani_marine": [2],
    "solsec": [2],
    "spirit_singer": [2],
    "storm_knight_inconstant_star": [2],
    "storm_knight_shadows": [2],
    "storm_knight_thunder": [2],
    "truther": [2],
    "vargr_army": [2],
    "vargr_citizen": [2],
    "vargr_corsair": [2],
    "vargr_emissary": [2],
    "vargr_law_enforcement": [2],
    "vargr_loner": [2],
    "vargr_marines": [2],
    "vargr_merchant": [2],
    "vargr_navy": [2],
    "vargr_psion": [2],
    "vargr_scientist": [2],
    "zhodani_agent": [2],
    "zhodani_army": [2],
    "zhodani_entertainer": [2],
    "zhodani_government": [2],
    "zhodani_guard": [2],
    "zhodani_merchant": [2],
    "zhodani_navy": [2],
    "zhodani_scholar": [2],
}

# Careers with mishaps that need career_continues added
mishap_needs_cc = {
    "aslan_spacer": [5],
    "confederation_navy": [2],
    "ge_fleet": [3],
}

# Careers with events that have "lose all benefits" text but missing forfeit_all_benefits
event_needs_forfeit_all = {
    "aslan_military_officer": [10],
    "aslan_space_officer": [10],
    "believer": [9],
    "ge_fleet_officer": [3],  # event 3 not 10
    "ge_warrior_officer": [10],
}

# Careers with mishaps that have "lose all benefits" text but missing forfeit_all_benefits
mishap_needs_forfeit_all = {
    "aslan_outcast": [2],
}

event_effects = lifepath._EVENT_EFFECTS
mishap_effects = lifepath._MISHAP_EFFECTS

total_patches = 0

print("Analyzing what needs to be patched...")
print()

# Check Event 2 entries
for career_id, event_nums in event2_needs_cc.items():
    if career_id not in event_effects:
        print(f"WARN: {career_id} not in _EVENT_EFFECTS")
        continue

    for event_num in event_nums:
        if event_num not in event_effects[career_id]:
            print(f"WARN: {career_id} event {event_num} not in _EVENT_EFFECTS")
            continue

        effects = event_effects[career_id][event_num]

        # Check if career_continues is already there
        has_cc = any(e.get("type") == "career_continues" for e in effects)

        # Check if trigger_disaster_mishap is there
        has_disaster = any(e.get("type") == "trigger_disaster_mishap" for e in effects)

        if has_disaster and not has_cc:
            print(f"Need career_continues: {career_id} event {event_num}")
            total_patches += 1

# Check event forfeit_all_benefits
for career_id, event_nums in event_needs_forfeit_all.items():
    if career_id not in event_effects:
        continue

    for event_num in event_nums:
        if event_num not in event_effects[career_id]:
            continue

        effects = event_effects[career_id][event_num]
        has_ff = any(e.get("type") == "forfeit_all_benefits" for e in effects)
        has_cc = any(
            e.get("type") == "skill_check" and
            any(eff.get("type") == "forfeit_all_benefits" for eff in e.get("on_fail", []))
            for e in effects
        )

        if not has_ff and not has_cc:
            print(f"Need forfeit_all_benefits: {career_id} event {event_num}")
            total_patches += 1

# Check mishap needs
for career_id, mishap_nums in mishap_needs_cc.items():
    if career_id not in mishap_effects:
        continue

    for mishap_num in mishap_nums:
        if mishap_num not in mishap_effects[career_id]:
            continue

        effects = mishap_effects[career_id][mishap_num]
        has_cc = any(e.get("type") == "career_continues" for e in effects)

        if not has_cc:
            print(f"Need career_continues: {career_id} mishap {mishap_num}")
            total_patches += 1

# Check mishap forfeit_all_benefits
for career_id, mishap_nums in mishap_needs_forfeit_all.items():
    if career_id not in mishap_effects:
        continue

    for mishap_num in mishap_nums:
        if mishap_num not in mishap_effects[career_id]:
            continue

        effects = mishap_effects[career_id][mishap_num]
        has_ff = any(e.get("type") == "forfeit_all_benefits" for e in effects)

        if not has_ff:
            print(f"Need forfeit_all_benefits: {career_id} mishap {mishap_num}")
            total_patches += 1

print()
print(f"Total patches needed: {total_patches}")
print()
print("Note: This is a diagnostic run. To apply fixes, use manual Edit tool calls.")
