"""
Find all pending_choice BLOCK IDs (not option IDs within choices).
Cross-check handlers in resolve_career_mishap_choice.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find pending_choice block IDs — the "id" that comes right after "type": "pending_choice"
# Pattern: {"type": "pending_choice", "id": "CHOICE_ID", ...}
pending_choice_ids = set(re.findall(
    r'"type":\s*"pending_choice"[^}]{0,100}?"id":\s*"([^"]+)"',
    content, re.DOTALL
))

print(f"Total unique pending_choice block IDs: {len(pending_choice_ids)}")

# Find all handlers
handled_by_eq = set(re.findall(r'elif\s+choice_id\s*==\s*"([^"]+)"', content))
handled_by_in_blocks = re.findall(r'elif\s+choice_id\s+in\s*\(([^)]+)\)', content)
handled_by_in = set()
for block in handled_by_in_blocks:
    for m in re.finditer(r'"([^"]+)"', block):
        handled_by_in.add(m.group(1))

all_handled = handled_by_eq | handled_by_in

# Unhandled
unhandled = pending_choice_ids - all_handled
if unhandled:
    print(f"\nUnhandled pending_choice block IDs ({len(unhandled)}):")
    for cid in sorted(unhandled):
        print(f"  {cid}")
else:
    print("All pending_choice block IDs have handlers!")

# Handlers with no matching static pending_choice definition
extra_handlers = all_handled - pending_choice_ids
# Filter out generic/dynamic ones
noise = {
    "mishap_victim", "mishap_deal", "army_join_cooperate",
    "skill_check",  # generic handler
}
real_extras = {h for h in extra_handlers if not any(h.startswith(p) for p in
    ('event_', 'droyne_', 'mishap_'))} - noise
if real_extras:
    print(f"\nHandlers with no static pending_choice definition ({len(real_extras)}):")
    for h in sorted(real_extras):
        print(f"  {h}")
