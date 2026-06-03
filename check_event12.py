"""
List all event 12 entries to verify they're appropriate (most should have auto_advance).
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()
    lines = content.split('\n')

# Find _EVENT_EFFECTS section
event_start = next((i for i, l in enumerate(lines) if '_EVENT_EFFECTS' in l and '=' in l), None)
if not event_start:
    print("Could not find _EVENT_EFFECTS")
    exit()

print(f"_EVENT_EFFECTS starts at line {event_start}")

current_career = None
event12_entries = []

for i in range(event_start, len(lines)):
    line = lines[i]
    career_match = re.match(r'\s+"([a-z_]+)":\s*\{', line)
    if career_match:
        current_career = career_match.group(1)

    event12_match = re.match(r'\s+12:\s*(.+)', line)
    if event12_match and current_career:
        entry = event12_match.group(1).strip()
        event12_entries.append((current_career, entry[:100]))

print(f"\nTotal event 12 entries: {len(event12_entries)}")
print("\nNon-auto_advance event 12s:")
for career, entry in event12_entries:
    if 'auto_advance' not in entry:
        print(f"  {career}: {entry[:90]}")

print("\nAll event 12 entries with auto_advance:")
count = sum(1 for _, e in event12_entries if 'auto_advance' in e)
print(f"  {count} of {len(event12_entries)} have auto_advance")
