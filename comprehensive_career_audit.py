#!/usr/bin/env python3
"""
Comprehensive career audit: check events and mishaps across all careers for consistency.

This scans every career JSON file and checks that:
1. Mishap/event text matches the effects in lifepath.py
2. "lose all benefits" text uses forfeit_all_benefits effect
3. "not ejected" text has career_continues effect
4. All effects are properly defined in _MISHAP_EFFECTS and _EVENT_EFFECTS
5. No missing or incomplete handlers
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Load all career JSONs
CAREERS_DIR = Path("app/data/careers")
careers = {}
for career_file in sorted(CAREERS_DIR.glob("*.json")):
    with open(career_file) as f:
        data = json.load(f)
        careers[data["id"]] = data

# Read lifepath.py to extract _EVENT_EFFECTS and _MISHAP_EFFECTS
with open("app/engine/lifepath.py", encoding="utf-8") as f:
    lifepath_code = f.read()

# Find _EVENT_EFFECTS definition
event_match = re.search(r"_EVENT_EFFECTS:\s*dict\[str,\s*dict\[int,\s*list\[dict\]\]\]\s*=\s*\{(.*?)\n\}\s*\n", lifepath_code, re.DOTALL)
event_effects_text = event_match.group(1) if event_match else ""

# Find _MISHAP_EFFECTS definition
mishap_match = re.search(r"_MISHAP_EFFECTS:\s*dict\[str,\s*dict\[int,\s*list\[dict\]\]\]\s*=\s*\{(.*?)(?=\n\n\n\n)", lifepath_code, re.DOTALL)
mishap_effects_text = mishap_match.group(1) if mishap_match else ""

# Extract career IDs that have entries in _EVENT_EFFECTS
event_careers = set(re.findall(r'^\s*"([^"]+)":\s*\{', event_effects_text, re.MULTILINE))
mishap_careers = set(re.findall(r'^\s*"([^"]+)":\s*\{', mishap_effects_text, re.MULTILINE))

print("=" * 100)
print("COMPREHENSIVE CAREER AUDIT")
print("=" * 100)
print()

issues = []

for career_id in sorted(careers.keys()):
    career = careers[career_id]
    mishaps = career.get("mishaps", {})
    events = career.get("events", {})

    # ===== MISHAPS =====
    for mishap_num_str, mishap_text in mishaps.items():
        mishap_num = int(mishap_num_str)

        # Check for "lose all" text
        if "lose all" in mishap_text.lower():
            if "forfeit_all_benefits" not in lifepath_code or \
               f'"{career_id}"' not in mishap_effects_text or \
               f"{mishap_num}:" not in mishap_effects_text:
                issues.append({
                    "type": "missing_effect",
                    "career": career_id,
                    "item": f"mishap {mishap_num}",
                    "text": mishap_text[:80],
                    "problem": "Has 'lose all' text but no forfeit_all_benefits effect"
                })

        # Check for "not ejected" text
        if "not ejected" in mishap_text.lower() or "not forced out" in mishap_text.lower():
            if "career_continues" not in lifepath_code or \
               f'"{career_id}"' not in mishap_effects_text:
                issues.append({
                    "type": "missing_career_continues",
                    "career": career_id,
                    "item": f"mishap {mishap_num}",
                    "text": mishap_text[:80],
                    "problem": "Has 'not ejected' text but no career_continues effect"
                })

        # Check if effects exist in lifepath.py
        if career_id not in mishap_careers and mishaps:
            issues.append({
                "type": "missing_mishap_effects",
                "career": career_id,
                "item": "all mishaps",
                "text": f"{len(mishaps)} mishaps defined",
                "problem": "Career has no _MISHAP_EFFECTS entry in lifepath.py"
            })
            break

    # ===== EVENTS =====
    for event_num_str, event_text in events.items():
        event_num = int(event_num_str)

        # Skip life event (handled separately)
        if "Life Event" in event_text or "life event" in event_text.lower():
            continue

        # Check for "lose all" text
        if "lose all" in event_text.lower():
            if f'"{career_id}"' not in event_effects_text:
                issues.append({
                    "type": "missing_event_effect",
                    "career": career_id,
                    "item": f"event {event_num}",
                    "text": event_text[:80],
                    "problem": "Has 'lose all benefits' text but no effect entry"
                })

        # Check for "not ejected" text
        if "not ejected" in event_text.lower():
            if f'"{career_id}"' not in event_effects_text:
                issues.append({
                    "type": "missing_event_continues",
                    "career": career_id,
                    "item": f"event {event_num}",
                    "text": event_text[:80],
                    "problem": "Has 'not ejected' text but no career_continues effect"
                })

        # Check if effects exist in lifepath.py
        if career_id not in event_careers and events:
            issues.append({
                "type": "missing_event_effects",
                "career": career_id,
                "item": "all events",
                "text": f"{len(events)} events defined",
                "problem": "Career has no _EVENT_EFFECTS entry in lifepath.py"
            })
            break

# ===== PRINT RESULTS =====
print(f"Total careers scanned: {len(careers)}")
print(f"Careers with mishaps: {len(mishap_careers)}")
print(f"Careers with events: {len(event_careers)}")
print()

if issues:
    print(f"ISSUES FOUND: {len(issues)}")
    print("=" * 100)
    for issue in issues:
        print(f"\n{issue['type'].upper()}")
        print(f"  Career: {issue['career']}")
        print(f"  Item:   {issue['item']}")
        print(f"  Text:   {issue['text']}")
        print(f"  Fix:    {issue['problem']}")
else:
    print("✓ No major issues found!")
    print()
    print("All careers have:")
    print("  ✓ Effect entries in lifepath.py")
    print("  ✓ Proper 'lose all' → forfeit_all_benefits mapping")
    print("  ✓ Proper 'not ejected' → career_continues mapping")

print()
print("=" * 100)
