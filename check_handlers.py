"""
Cross-check: find all pending_choice IDs used in _EVENT_EFFECTS and _MISHAP_EFFECTS
and verify each has a handler in resolve_career_mishap_choice.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8') as f:
    content = f.read()

# Find all pending_choice IDs in effect tables
table_ids = set(re.findall(r'"id":\s*"(event_[^"]+)"', content))
print(f"Total event_* pending_choice IDs in tables: {len(table_ids)}")

# Find all elif choice_id == "..." handler definitions
handler_ids = set(re.findall(r'elif\s+choice_id\s*==\s*"(event_[^"]+)"', content))
print(f"Total event_* handlers: {len(handler_ids)}")

# Missing handlers
missing = table_ids - handler_ids
if missing:
    print("\nMISSING HANDLERS for:")
    for m in sorted(missing):
        print(f"  {m}")
else:
    print("\nAll event_* pending_choice IDs have handlers!")

# Extra handlers (handlers with no matching table entry - dead code)
extra = handler_ids - table_ids
if extra:
    print("\nExtra handlers (no matching table entry):")
    for e in sorted(extra):
        print(f"  {e}")
