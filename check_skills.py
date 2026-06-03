import re, json

with open('app/engine/lifepath.py', encoding='utf-8') as f:
    content = f.read()

with open('app/data/tables/skills.json', encoding='utf-8') as f:
    skills_data = json.load(f)

core_skills = set(s.lower() for s in skills_data.get('core', []))
speciality_map = {k.lower(): [v.lower() for v in vs] for k, vs in skills_data.get('speciality', {}).items()}

# Print available skills for reference
print("Core skills:", sorted(core_skills))
print("Speciality bases:", sorted(speciality_map.keys()))
print()

# Extract all skill names from skill_choice / free_skill_choice options
# Look for "options": [...] patterns
option_blocks = re.findall(r'"options":\s*\[([^\]]+)\]', content)
raw_skills = set()
for block in option_blocks:
    names = re.findall(r'"([^"]+)"', block)
    for n in names:
        raw_skills.add(n)

print(f'Total unique strings in skill_choice options: {len(raw_skills)}')

# Validate each
KNOWN_NON_SKILLS = {
    'soc', 'dm4', 'dm3', 'dm2', 'skill', 'stat', 'auto', 'ransom', 'free',
    'benefit', 'refuse', 'accept', 'injury', 'nothing', 'ally', 'rival',
}

unknown = []
for name in sorted(raw_skills):
    nl = name.lower()

    # Skip obvious non-skill option IDs
    if nl in KNOWN_NON_SKILLS:
        continue
    if nl.startswith('contact') or nl.startswith('enemy') or nl.startswith('ally'):
        continue
    if nl.startswith('gain ') or nl.startswith('dm+') or nl.startswith('dm-') or nl.startswith('soc '):
        continue
    if len(name) > 40:  # Long labels, not skill names
        continue

    # Check speciality form: "Skill (spec)"
    m = re.match(r'^(.+?) \((.+)\)$', name)
    if m:
        base = m.group(1).lower()
        spec = m.group(2).lower()
        if base in speciality_map:
            valid_specs = speciality_map[base]
            if spec not in valid_specs:
                unknown.append(f'INVALID SPEC: "{name}" — valid specs for {m.group(1)}: {speciality_map[base]}')
        elif base not in core_skills:
            unknown.append(f'UNKNOWN SKILL (with spec): "{name}"')
        # else: base is core skill, spec may be custom (alien career)
    else:
        # Plain skill name
        if nl not in core_skills and nl not in speciality_map:
            unknown.append(f'UNKNOWN PLAIN: "{name}"')

if unknown:
    print('Issues:')
    for u in unknown:
        safe_u = u.encode('ascii', errors='replace').decode('ascii')
        print(' ', safe_u)
else:
    print('All skill names appear valid!')
