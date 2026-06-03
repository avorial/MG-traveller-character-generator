#!/usr/bin/env python3
"""Generate detailed audit report and save to file."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "app"))
sys.path.insert(0, str(Path.cwd()))

from engine import lifepath

CAREERS_DIR = Path("app/data/careers")
careers = {}
for career_file in sorted(CAREERS_DIR.glob("*.json")):
    with open(career_file, encoding='utf-8') as f:
        data = json.load(f)
        careers[data["id"]] = data

event_effects = lifepath._EVENT_EFFECTS
mishap_effects = lifepath._MISHAP_EFFECTS

issues = []

# Collect all issues
for career_id in sorted(careers.keys()):
    career = careers[career_id]

    # MISHAPS
    mishaps = career.get("mishaps", {})
    if mishaps:
        if career_id not in mishap_effects:
            issues.append(("CRITICAL", career_id, "all mishaps",
                          "NO _MISHAP_EFFECTS entry", f"{len(mishaps)} mishaps"))
        else:
            mishap_data = mishap_effects[career_id]
            for mishap_num_str, mishap_text in mishaps.items():
                mishap_num = int(mishap_num_str)
                if mishap_num not in mishap_data:
                    issues.append(("CRITICAL", career_id, f"mishap {mishap_num}",
                                  "Missing from _MISHAP_EFFECTS", mishap_text[:80]))
                else:
                    effects = mishap_data[mishap_num]
                    # Text mismatches
                    if "lose all" in mishap_text.lower():
                        has_ff = any(e.get("type") == "forfeit_all_benefits" for e in effects)
                        if not has_ff:
                            issues.append(("MEDIUM", career_id, f"mishap {mishap_num}",
                                          "'lose all benefits' but no forfeit_all_benefits", mishap_text[:80]))

                    if "not ejected" in mishap_text.lower() or "not forced out" in mishap_text.lower():
                        has_cc = any(e.get("type") == "career_continues" for e in effects)
                        if not has_cc:
                            issues.append(("MEDIUM", career_id, f"mishap {mishap_num}",
                                          "'not ejected' but no career_continues", mishap_text[:80]))

    # EVENTS
    events = career.get("events", {})
    if events:
        if career_id not in event_effects:
            issues.append(("CRITICAL", career_id, "all events",
                          "NO _EVENT_EFFECTS entry", f"{len(events)} events"))
        else:
            event_data = event_effects[career_id]
            for event_num_str, event_text in events.items():
                event_num = int(event_num_str)

                if "life event" in event_text.lower():
                    continue

                if event_num not in event_data:
                    issues.append(("CRITICAL", career_id, f"event {event_num}",
                                  "Missing from _EVENT_EFFECTS", event_text[:80]))
                else:
                    effects = event_data[event_num]

                    if "lose all" in event_text.lower():
                        has_ff = any(
                            (e.get("type") == "forfeit_all_benefits") or
                            (e.get("type") == "skill_check" and
                             any(eff.get("type") == "forfeit_all_benefits" for eff in e.get("on_fail", [])))
                            for e in effects
                        )
                        if not has_ff:
                            issues.append(("MEDIUM", career_id, f"event {event_num}",
                                          "'lose all benefits' but no forfeit_all_benefits", event_text[:80]))

                    if "not ejected" in event_text.lower():
                        has_cc = any(
                            (e.get("type") == "career_continues") or
                            (e.get("type") == "skill_check" and
                             any(eff.get("type") == "career_continues" for eff in e.get("on_pass", []) + e.get("on_fail", [])))
                            for e in effects
                        )
                        if not has_cc:
                            issues.append(("MEDIUM", career_id, f"event {event_num}",
                                          "'not ejected' but no career_continues", event_text[:80]))

# Write report
with open("AUDIT_REPORT.txt", "w", encoding='utf-8') as f:
    f.write("=" * 120 + "\n")
    f.write("COMPREHENSIVE CAREER AUDIT REPORT\n")
    f.write("=" * 120 + "\n\n")

    critical = [i for i in issues if i[0] == "CRITICAL"]
    medium = [i for i in issues if i[0] == "MEDIUM"]

    f.write("SUMMARY\n")
    f.write("-" * 120 + "\n")
    f.write("Total Issues: {}\n".format(len(issues)))
    f.write("  CRITICAL: {}\n".format(len(critical)))
    f.write("  MEDIUM: {}\n\n".format(len(medium)))

    f.write("=" * 120 + "\n")
    f.write("CRITICAL ISSUES (must fix)\n")
    f.write("=" * 120 + "\n\n")

    for severity, career, item, problem, detail in sorted(critical, key=lambda x: (x[1], x[2])):
        f.write("Career: {}\n".format(career))
        f.write("  Item:    {}\n".format(item))
        f.write("  Problem: {}\n".format(problem))
        f.write("  Detail:  {}\n\n".format(detail))

    f.write("\n")
    f.write("=" * 120 + "\n")
    f.write("MEDIUM ISSUES (should fix)\n")
    f.write("=" * 120 + "\n\n")

    for severity, career, item, problem, detail in sorted(medium, key=lambda x: (x[1], x[2])):
        f.write("Career: {}\n".format(career))
        f.write("  Item:    {}\n".format(item))
        f.write("  Problem: {}\n".format(problem))
        f.write("  Detail:  {}\n\n".format(detail))

print("Report saved to AUDIT_REPORT.txt")
print("{} total issues found".format(len(issues)))
print("{} CRITICAL, {} MEDIUM".format(len(critical), len(medium)))
