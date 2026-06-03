"""
Cross-check: find all pending_choice IDs used in _MISHAP_EFFECTS
and verify each has a handler in resolve_career_mishap_choice.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8') as f:
    content = f.read()

# Find all mishap pending_choice IDs (mishap_* prefix)
mishap_table_ids = set(re.findall(r'"id":\s*"(mishap_[^"]+)"', content))
print(f"Total mishap_* pending_choice IDs in tables: {len(mishap_table_ids)}")

# Find all handlers
mishap_handler_ids = set(re.findall(r'elif\s+choice_id\s*==\s*"(mishap_[^"]+)"', content))
print(f"Total mishap_* handlers: {len(mishap_handler_ids)}")

missing = mishap_table_ids - mishap_handler_ids
if missing:
    print("\nMISSING HANDLERS for:")
    for m in sorted(missing):
        print(f"  {m}")
else:
    print("\nAll mishap_* pending_choice IDs have handlers!")

extra = mishap_handler_ids - mishap_table_ids
if extra:
    print("\nExtra handlers (no matching table entry):")
    for e in sorted(extra):
        print(f"  {e}")

# Also check for any "pending_choice" IDs without a specific prefix
other_ids = set(re.findall(r'"id":\s*"([^"]+)"', content))
event_or_mishap = {i for i in other_ids if i.startswith('event_') or i.startswith('mishap_')}
other_pending = other_ids - event_or_mishap
# Filter to only those that appear as pending_choice IDs (need more context)
print(f"\nOther IDs in tables (not event_/mishap_): {len(other_pending)}")
for i in sorted(other_pending):
    if len(i) > 2 and not i.isdigit():
        print(f"  {i}")
