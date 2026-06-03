#!/usr/bin/env python3
"""Fix the final 22 medium-severity issues"""

from pathlib import Path

filepath = Path("app/engine/lifepath.py")
with open(filepath, encoding='utf-8') as f:
    lines = f.readlines()

# Issues to fix (career, event/mishap num, type, effect_to_add)
fixes_needed = [
    # Event 10 duel - add forfeit_all_benefits to on_fail
    ("aslan_military_officer", 10, "event", "forfeit_all_benefits"),
    ("aslan_space_officer", 10, "event", "forfeit_all_benefits"),
    ("ge_fleet_officer", 10, "event", "forfeit_all_benefits"),
    ("ge_warrior_officer", 10, "event", "forfeit_all_benefits"),

    # Mishaps - add forfeit_all_benefits or career_continues
    ("aslan_outcast", 2, "mishap", "forfeit_all_benefits"),
    ("believer", 9, "event", "forfeit_all_benefits"),
    ("aslan_spacer", 5, "mishap", "career_continues"),
    ("confederation_navy", 2, "mishap", "career_continues"),
    ("ge_fleet", 3, "mishap", "career_continues"),
    ("ge_fleet_officer", 2, "mishap", "forfeit_all_benefits"),
    ("ge_landless_one", 2, "mishap", "forfeit_all_benefits"),

    # Events with "not ejected" - add career_continues
    ("drifter", 6, "event", "career_continues"),
    ("merchant", 3, "event", "career_continues"),
    ("merchant", 9, "event", "career_continues"),
    ("navy", 3, "event", "career_continues"),
    ("rogue", 3, "event", "career_continues"),
    ("rogue", 8, "event", "career_continues"),
    ("scout", 8, "event", "career_continues"),
    ("scout", 10, "event", "career_continues"),
    ("solsec", 5, "event", "career_continues"),
]

changes = 0

# Process each fix
for career, num, item_type, effect in fixes_needed:
    # Simple approach: search for the pattern and add the effect if missing
    pattern_to_find = f'"{career}"'

    found = False
    for i, line in enumerate(lines):
        if pattern_to_find in line and item_type in line:
            # Found career definition, now look for the event/mishap
            for j in range(i, min(i+200, len(lines))):
                if f'{num}:' in lines[j] and '[' in lines[j]:
                    # Found the event/mishap
                    # Check if effect is already there
                    context_lines = ''.join(lines[j:min(j+30, len(lines))])
                    if effect not in context_lines:
                        # Need to add it
                        # For now, just count
                        changes += 1
                        print(f"Would fix: {career} {item_type} {num} - add {effect}")
                        found = True
                    break
            if found:
                break

print(f"\nTotal fixes identified: {changes}")
print("\nNote: Manual fixes needed for the final 22 issues")
print("These require careful placement within skill_check on_fail or event lists")
