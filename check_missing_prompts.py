"""
Find skill_check entries in event/mishap TABLES that have no "prompt" key.
Tables start around line 10000 but mishap tables also start earlier (~line 12440).
Search the whole _MISHAP_EFFECTS and _EVENT_EFFECTS sections.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()
    lines = content.split('\n')

# Find all skill_check blocks that lack a "prompt" key
# A skill_check block ends when we hit another key or closing bracket

# Strategy: find all {"type": "skill_check", ...} blocks in table section (line 10000+)
# and check if they contain "prompt"

# Find table section start
table_markers = [i for i, l in enumerate(lines) if '_EVENT_EFFECTS' in l or '_MISHAP_EFFECTS' in l]
print("Table section markers at lines:", table_markers[:5])

# Search for skill_check patterns that don't have prompt
# We'll look for {"type": "skill_check" followed by closing "}]" without a "prompt" key
skill_check_pattern = re.compile(
    r'"type":\s*"skill_check",\s*'
    r'"skills":.*?'
    r'"target":\s*\d+,\s*'
    r'"on_nat2":.*?'
    r'"on_(?:pass|fail)":[^\]]*\]'
    r'(?:.*?"on_(?:pass|fail)":[^\]]*\])*'
    r'\}',
    re.DOTALL
)

# Simpler: just find all skill_check blocks in event tables and check for "prompt"
# Find all occurrences of skill_check in the content after line 10000
table_content_start = '\n'.join(lines[9999:])
offset_to_add = 9999

# Find all skill_check blocks
sc_starts = [m.start() for m in re.finditer(r'"type":\s*"skill_check"', table_content_start)]
print(f"\nTotal skill_check occurrences in table section: {len(sc_starts)}")

missing_prompt = []
for start in sc_starts:
    # Extract a reasonable window around the skill_check
    window = table_content_start[start:start+600]
    # Find the closing of this effect dict (count braces)
    depth = 0
    end = 0
    # Find the opening { that starts this dict
    brace_start = table_content_start.rfind('{', 0, start)
    if brace_start == -1:
        continue
    # Walk from brace_start to find the matching }
    for i in range(brace_start, min(brace_start + 800, len(table_content_start))):
        if table_content_start[i] == '{':
            depth += 1
        elif table_content_start[i] == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == 0:
        continue
    block = table_content_start[brace_start:end+1]
    has_prompt = '"prompt"' in block
    if not has_prompt:
        lineno = offset_to_add + table_content_start[:start].count('\n') + 1
        # Extract a short snippet
        snippet = block[:150].replace('\n', ' ').strip()
        missing_prompt.append((lineno, snippet))

print(f"\nskill_check entries without 'prompt' in tables: {len(missing_prompt)}")
for lineno, snippet in missing_prompt:
    safe = snippet.encode('ascii', errors='replace').decode('ascii')
    print(f"  Line ~{lineno}: {safe[:120]}")
