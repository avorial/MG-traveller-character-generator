"""
Find skill_check effects (in EVENT/MISHAP TABLES only, lines 10000+) where
on_pass is [] but the prompt mentions a pass consequence.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Only look in the table section (after line 10000)
lines = content.split('\n')
table_start = 10000
table_content = '\n'.join(lines[table_start:])

# Find skill_check blocks with on_pass: [] but prompt mentions pass effect
pattern = re.compile(
    r'"type":\s*"skill_check".*?"on_pass":\s*\[\].*?"prompt":\s*"([^"]*)"',
    re.DOTALL
)

suspicious = []
for m in pattern.finditer(table_content):
    prompt = m.group(1)
    prompt_lower = prompt.lower()
    has_pass_mention = any([
        ': pass' in prompt_lower,
        '; pass' in prompt_lower,
        'pass:' in prompt_lower,
        'on pass' in prompt_lower,
        'succeed' in prompt_lower,
    ])
    if has_pass_mention:
        lineno = table_start + table_content[:m.start()].count('\n') + 1
        suspicious.append((lineno, prompt[:130]))

print(f"skill_check in tables with empty on_pass but prompt mentions pass: {len(suspicious)}")
for lineno, prompt in suspicious:
    safe = prompt.encode('ascii', errors='replace').decode('ascii')
    print(f"  Line ~{lineno}: {safe}")
