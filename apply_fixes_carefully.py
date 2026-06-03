#!/usr/bin/env python3
"""
Apply medium-issue fixes more carefully by properly parsing the structure.
"""

from pathlib import Path
import re

filepath = Path("app/engine/lifepath.py")
with open(filepath, encoding='utf-8') as f:
    lines = f.readlines()

# List of careers that need Event 2 career_continues fix
event2_careers = [
    "agent", "army", "aslan_ceremonial", "aslan_envoy", "aslan_management",
    "aslan_military", "aslan_outcast", "aslan_scientist", "aslan_spacer",
    "aslan_wanderer", "citizen", "confederation_army", "confederation_navy",
    "dolphin_civilian", "dolphin_military", "entertainer", "ge_fleet",
    "ge_landless_one", "ge_slave", "ge_warrior", "girug_kagh_translator",
    "hiver_academic", "hiver_generalist", "hiver_manipulator", "hiver_merchant",
    "kkree_merchant", "kkree_noble", "kkree_pastoral", "kkree_servant",
    "marine", "merchant", "navy", "noble", "party", "philosopher_elder",
    "prisoner", "psion", "scholar", "scout", "solomani_marine", "solsec",
    "spirit_singer", "storm_knight_inconstant_star", "storm_knight_shadows",
    "storm_knight_thunder", "truther", "vargr_army", "vargr_citizen",
    "vargr_corsair", "vargr_emissary", "vargr_law_enforcement", "vargr_loner",
    "vargr_marines", "vargr_merchant", "vargr_navy", "vargr_psion",
    "vargr_scientist", "zhodani_agent", "zhodani_army", "zhodani_entertainer",
    "zhodani_government", "zhodani_guard", "zhodani_merchant", "zhodani_navy",
    "zhodani_scholar",
]

changes = []

# Find and fix each career's Event 2
for i, line in enumerate(lines):
    # Look for event 2 entries that have trigger_disaster_mishap but not career_continues
    if '2:  [{"type": "trigger_disaster_mishap"}],' in line:
        # Check if career_continues is already there
        if 'career_continues' not in line:
            # Replace }], with }, {"type": "career_continues"}],
            new_line = line.replace(
                '2:  [{"type": "trigger_disaster_mishap"}],',
                '2:  [{"type": "trigger_disaster_mishap"}, {"type": "career_continues"}],'
            )
            lines[i] = new_line
            # Identify which career this is
            for j in range(i-1, max(0, i-20), -1):
                if '": {' in lines[j]:
                    career_name = lines[j].split('"')[1]
                    if career_name in event2_careers:
                        changes.append(f"Fixed Event 2 for {career_name}")
                    break

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Applied {len(changes)} fixes:")
for change in changes:
    print(f"  {change}")

if not changes:
    print("No fixes were applied")
else:
    print(f"\nFile updated successfully! Total fixes: {len(changes)}")
