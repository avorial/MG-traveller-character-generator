"""
Find skill_check effects where on_fail is [] but the prompt mentions a fail consequence.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find skill_check blocks with on_fail: []
# Pattern: capture the whole skill_check dict
pattern = re.compile(
    r'"type":\s*"skill_check".*?"on_fail":\s*\[\].*?"prompt":\s*"([^"]*)"',
    re.DOTALL
)

fail_keywords = ['fail', 'loss', 'lose', 'minus', 'injury', 'eject', 'end', 'remove', 'penalt', 'wrong', 'cost']

suspicious = []
for m in pattern.finditer(content):
    prompt = m.group(1)
    prompt_lower = prompt.lower()
    # Check if prompt mentions fail consequences
    has_fail_mention = any([
        ': fail' in prompt_lower,
        '; fail' in prompt_lower,
        'fail:' in prompt_lower,
        'on fail' in prompt_lower,
    ])
    if has_fail_mention:
        # Find line number
        lineno = content[:m.start()].count('\n') + 1
        # Find career context
        career_search = content[:m.start()].rfind('"')
        # Just show a snippet
        snippet = content[m.start():m.start()+200].replace('\n', ' ')
        suspicious.append((lineno, prompt[:120]))

print(f"skill_check with empty on_fail but prompt mentions fail: {len(suspicious)}")
for lineno, prompt in suspicious:
    safe = prompt.encode('ascii', errors='replace').decode('ascii')
    print(f"  Line ~{lineno}: {safe}")
