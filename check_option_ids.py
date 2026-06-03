"""
Find all pending_choice option IDs used in event/mishap tables.
Cross-check that each (choice_id, option_id) pair is handled in the resolve functions.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find all pending_choice blocks with id and options
pending_pattern = re.compile(
    r'"type":\s*"pending_choice",\s*"id":\s*"([^"]+)".*?"options":\s*\[([^\]]*)\]',
    re.DOTALL
)

choice_options = {}
for m in pending_pattern.finditer(content):
    choice_id = m.group(1)
    options_block = m.group(2)
    option_ids = re.findall(r'"id":\s*"([^"]+)"', options_block)
    if option_ids:
        choice_options.setdefault(choice_id, set()).update(option_ids)

print(f"Total pending_choice types with options: {len(choice_options)}")

# For each choice_id, check what options the handler handles
# Look for the handler: "elif choice_id == "X":"
# and find option checking patterns like: "if selected == 'Y'" or "selected in ('A','B')"
issues = []
for choice_id, option_ids in sorted(choice_options.items()):
    # Find handler section
    handler_pattern = re.compile(rf'elif choice_id == "{re.escape(choice_id)}"(.+?)(?=elif choice_id|def [a-z])', re.DOTALL)
    m = handler_pattern.search(content)
    if not m:
        # Check if it's handled by generic opt handler
        if len(option_ids) <= 4:  # Small number of options might be generic
            issues.append(f"NO HANDLER: {choice_id} (options: {sorted(option_ids)[:4]})")
        continue
    handler_body = m.group(1)
    # Check each option id
    for opt_id in option_ids:
        if opt_id not in handler_body:
            issues.append(f"OPTION NOT HANDLED: {choice_id}.{opt_id}")

if issues:
    print("\nPotential issues:")
    for issue in issues[:30]:
        print(f"  {issue}")
else:
    print("All pending_choice options appear handled!")
