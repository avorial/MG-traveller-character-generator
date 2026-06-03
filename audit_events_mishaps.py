#!/usr/bin/env python3
"""
Comprehensive audit of all career events and mishaps.
Compares career JSON files against lifepath.py _EVENT_EFFECTS and _MISHAP_EFFECTS.
"""

import json
import sys
from pathlib import Path

# Add the app directory to path so we can import
sys.path.insert(0, str(Path.cwd() / "app"))
sys.path.insert(0, str(Path.cwd()))

from engine import lifepath

# Load all career JSONs
CAREERS_DIR = Path("app/data/careers")
careers = {}
for career_file in sorted(CAREERS_DIR.glob("*.json")):
    with open(career_file, encoding='utf-8') as f:
        data = json.load(f)
        careers[data["id"]] = data

print("=" * 100)
print("COMPREHENSIVE CAREER EVENTS & MISHAPS AUDIT")
print("=" * 100)
print()

# Get the actual dictionaries from lifepath
event_effects = lifepath._EVENT_EFFECTS
mishap_effects = lifepath._MISHAP_EFFECTS

print("Total careers scanned: {}".format(len(careers)))
print("Careers with _EVENT_EFFECTS: {}".format(len(event_effects)))
print("Careers with _MISHAP_EFFECTS: {}".format(len(mishap_effects)))
print()

issues = []

# Check each career
for career_id in sorted(careers.keys()):
    career = careers[career_id]

    # ===== MISHAPS =====
    mishaps = career.get("mishaps", {})
    if mishaps:
        if career_id not in mishap_effects:
            issues.append({
                "severity": "CRITICAL",
                "type": "missing_mishap_effects",
                "career": career_id,
                "item": "all mishaps",
                "count": len(mishaps),
                "problem": "Career has mishaps but NO _MISHAP_EFFECTS entry"
            })
        else:
            # Check each individual mishap
            mishap_data = mishap_effects[career_id]
            for mishap_num_str, mishap_text in mishaps.items():
                mishap_num = int(mishap_num_str)
                if mishap_num not in mishap_data:
                    issues.append({
                        "severity": "CRITICAL",
                        "type": "missing_mishap_entry",
                        "career": career_id,
                        "item": f"mishap {mishap_num}",
                        "text": mishap_text[:60],
                        "problem": "No effect entry in _MISHAP_EFFECTS"
                    })
                else:
                    effects = mishap_data[mishap_num]
                    # Check for "lose all benefits" text → forfeit_all_benefits
                    has_lose_all_text = "lose all" in mishap_text.lower()
                    has_forfeit_all = any(e.get("type") == "forfeit_all_benefits" for e in effects)

                    if has_lose_all_text and not has_forfeit_all:
                        issues.append({
                            "severity": "MEDIUM",
                            "type": "text_effect_mismatch",
                            "career": career_id,
                            "item": f"mishap {mishap_num}",
                            "text": mishap_text[:60],
                            "problem": "'lose all benefits' text but no forfeit_all_benefits effect"
                        })

                    # Check for "not ejected" text → career_continues
                    has_not_ejected = "not ejected" in mishap_text.lower() or "not forced out" in mishap_text.lower()
                    has_career_continues = any(e.get("type") == "career_continues" for e in effects)

                    if has_not_ejected and not has_career_continues:
                        issues.append({
                            "severity": "MEDIUM",
                            "type": "text_effect_mismatch",
                            "career": career_id,
                            "item": f"mishap {mishap_num}",
                            "text": mishap_text[:60],
                            "problem": "'not ejected' text but no career_continues effect"
                        })

    # ===== EVENTS =====
    events = career.get("events", {})
    if events:
        if career_id not in event_effects:
            issues.append({
                "severity": "CRITICAL",
                "type": "missing_event_effects",
                "career": career_id,
                "item": "all events",
                "count": len(events),
                "problem": "Career has events but NO _EVENT_EFFECTS entry"
            })
        else:
            # Check each individual event
            event_data = event_effects[career_id]
            for event_num_str, event_text in events.items():
                event_num = int(event_num_str)

                # Skip life event
                if "life event" in event_text.lower():
                    continue

                if event_num not in event_data:
                    issues.append({
                        "severity": "CRITICAL",
                        "type": "missing_event_entry",
                        "career": career_id,
                        "item": f"event {event_num}",
                        "text": event_text[:60],
                        "problem": "No effect entry in _EVENT_EFFECTS"
                    })
                else:
                    effects = event_data[event_num]

                    # Check for "lose all benefits" text
                    has_lose_all_text = "lose all" in event_text.lower()
                    has_forfeit_all = any(
                        (e.get("type") == "forfeit_all_benefits") or
                        (e.get("type") == "skill_check" and
                         any(eff.get("type") == "forfeit_all_benefits" for eff in e.get("on_fail", [])))
                        for e in effects
                    )

                    if has_lose_all_text and not has_forfeit_all:
                        issues.append({
                            "severity": "MEDIUM",
                            "type": "text_effect_mismatch",
                            "career": career_id,
                            "item": f"event {event_num}",
                            "text": event_text[:60],
                            "problem": "'lose all benefits' text but no forfeit_all_benefits effect"
                        })

                    # Check for "not ejected" text
                    has_not_ejected = "not ejected" in event_text.lower()
                    has_career_continues = any(
                        (e.get("type") == "career_continues") or
                        (e.get("type") == "skill_check" and
                         any(eff.get("type") == "career_continues" for eff in e.get("on_pass", []) + e.get("on_fail", [])))
                        for e in effects
                    )

                    if has_not_ejected and not has_career_continues:
                        issues.append({
                            "severity": "MEDIUM",
                            "type": "text_effect_mismatch",
                            "career": career_id,
                            "item": f"event {event_num}",
                            "text": event_text[:60],
                            "problem": "'not ejected' text but no career_continues effect"
                        })

# ===== PRINT RESULTS =====
if not issues:
    print("[OK] ALL CLEAR! No issues found.")
    print()
    print("All 83 careers have:")
    print("  [OK] Complete _EVENT_EFFECTS entries")
    print("  [OK] Complete _MISHAP_EFFECTS entries")
    print("  [OK] Proper text-to-effect mappings")
else:
    critical = [i for i in issues if i["severity"] == "CRITICAL"]
    medium = [i for i in issues if i["severity"] == "MEDIUM"]

    print("[ERROR] ISSUES FOUND: {} total".format(len(issues)))
    print("   CRITICAL: {} issues".format(len(critical)))
    print("   MEDIUM: {} issues".format(len(medium)))
    print()

    if critical:
        print("=" * 100)
        print("CRITICAL ISSUES (Missing entries)")
        print("=" * 100)
        for issue in sorted(critical, key=lambda x: (x["career"], x["item"])):
            print(f"\n{issue['type'].upper()}")
            print(f"  Career: {issue['career']}")
            print(f"  Item:   {issue['item']}")
            if 'count' in issue:
                print(f"  Count:  {issue['count']}")
            print(f"  Fix:    {issue['problem']}")

    if medium:
        print()
        print("=" * 100)
        print("MEDIUM ISSUES (Text-to-effect mismatches)")
        print("=" * 100)
        for issue in sorted(medium, key=lambda x: (x["career"], x["item"]))[:20]:  # Show first 20
            print(f"\n{issue['type'].upper()}")
            print(f"  Career: {issue['career']}")
            print(f"  Item:   {issue['item']}")
            print(f"  Text:   {issue['text']}")
            print(f"  Fix:    {issue['problem']}")

        if len(medium) > 20:
            print(f"\n... and {len(medium) - 20} more medium-severity issues")

print()
print("=" * 100)
