#!/usr/bin/env python3
"""Add event 7 to all Droyne careers in _EVENT_EFFECTS"""

from pathlib import Path

filepath = Path("app/engine/lifepath.py")
with open(filepath, encoding='utf-8') as f:
    lines = f.readlines()

droyne_careers = [
    "droyne_drone",
    "droyne_leader",
    "droyne_sport",
    "droyne_technician",
    "droyne_warrior",
    "droyne_worker",
]

changes = 0

# Find each droyne career in _EVENT_EFFECTS and add event 7 before event 8
for i, line in enumerate(lines):
    for career in droyne_careers:
        if f'"{career}": {{' in line:
            # Found a droyne career, now look for event 8 and add event 7 before it
            for j in range(i, min(i+100, len(lines))):
                if '8:  [' in lines[j] and 'type' in lines[j]:
                    # Found event 8, insert event 7 before it
                    indent = len(lines[j]) - len(lines[j].lstrip())
                    spaces = ' ' * indent
                    if '7:' not in ''.join(lines[j-5:j]):
                        # Event 7 not already there
                        lines.insert(j, f'{spaces}7:  [],  # Narrative event\n')
                        changes += 1
                        print(f"Added event 7 to {career}")
                    break
            break

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\nTotal additions: {changes}")
