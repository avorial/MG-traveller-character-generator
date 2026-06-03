"""Quick validation of new Spinward Extents species files."""
import json, os

BASE = r'C:\Users\patricthomas\TravllerCC_work\app\data\species'

NEW_SPECIES = [
    'aniyun', 'eslyat', 'freni_hybrid', 'freni_type1', 'freni_type2',
    'freni_type3', 'freni_type4', 'freni_type5', 'freni_type6',
    'ghenani', 'gmina', 'human_other', 'katangan', 'kemlae', 'ktiauao',
    'mal_gnar', 'murian', 'resavolk', 'teakhea', 'thonane', 'zhdianshe'
]

issues = []

for sid in NEW_SPECIES:
    path = os.path.join(BASE, sid + '.json')
    try:
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
    except Exception as e:
        issues.append(f'  PARSE ERROR {sid}: {e}')
        continue

    for req in ['id', 'name', 'description', 'characteristic_modifiers']:
        if req not in d:
            issues.append(f'  {sid}: missing field "{req}"')

    if d.get('id') != sid:
        issues.append(f'  {sid}: id mismatch — got "{d.get("id")}"')

    mods = d.get('characteristic_modifiers', {})
    custom = d.get('custom_characteristic_rolls', {})
    for stat in ['STR', 'DEX', 'END', 'INT', 'EDU', 'SOC']:
        if stat not in mods and stat not in custom:
            issues.append(f'  {sid}: no entry for {stat} in modifiers or custom_rolls')

    soc = d.get('societies', [])
    if not soc:
        issues.append(f'  {sid}: no societies field')

    print(f'  {sid}: ok')

print()
if issues:
    print(f'ISSUES ({len(issues)}):')
    for i in issues:
        print(i)
else:
    print('All new species valid — no issues found.')
