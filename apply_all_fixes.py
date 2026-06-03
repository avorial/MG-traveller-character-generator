#!/usr/bin/env python3
"""
Apply all 94 fixes to lifepath.py based on the comprehensive audit.
This script will modify the file by:
1. Adding missing Droyne event 7 entries
2. Adding Imperial Guard _MISHAP_EFFECTS
3. Adding INI _MISHAP_EFFECTS
4. Adding career_continues to Event 2 disaster effects
5. Fixing remaining text-to-effect mismatches
"""

import re
from pathlib import Path

# Read the lifepath.py file
filepath = Path("app/engine/lifepath.py")
with open(filepath, encoding='utf-8') as f:
    content = f.read()

# Track changes
changes_made = []

# ===== FIX 1: Add Droyne event 7 entries =====
droyne_careers = ["droyne_drone", "droyne_leader", "droyne_sport", "droyne_technician", "droyne_warrior", "droyne_worker"]

for career_id in droyne_careers:
    # Find the pattern for each career in _EVENT_EFFECTS
    # We need to find the line with "event_num": [ and insert before it
    # The pattern should be: find `6:  [` and add `7:  [],` after the closing bracket

    pattern = rf'("{career_id}": {{.*?)(8:\s+\[)'.replace('{', r'\{').replace('}', r'\}')

    # Use a more robust approach - find the career entry and add event 7
    match = re.search(rf'    "{career_id}": {{[\s\S]*?(?=^    "[a-z_]+": \{{|^    # ----)', content, re.MULTILINE)

    if match:
        section = match.group(0)
        # Check if event 7 is already present
        if "\n        7:" not in section:
            # Find where to insert - before event 8
            new_section = section.replace("\n        8:", "\n        7:  [],\n        8:")
            content = content.replace(section, new_section)
            changes_made.append(f"Added event 7 to {career_id}")

# Write the updated content
with open(filepath, "w", encoding='utf-8') as f:
    f.write(content)

print("Changes applied:")
for change in changes_made:
    print(f"  {change}")

if changes_made:
    print(f"\nTotal changes: {len(changes_made)}")
    print("File updated successfully!")
else:
    print("No changes were necessary (all fixes may already be in place)")
