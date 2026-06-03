"""
Check for suspicious DM effect patterns:
- dm_advancement with amount=0 (useless)
- dm_survival with large amounts (likely bug)
- stat effects with large amounts (likely bug)
- effect types that might be typos
"""
import re, json

with open('app/engine/lifepath.py', encoding='utf-8') as f:
    content = f.read()

KNOWN_EFFECT_TYPES = {
    'skill', 'skill_choice', 'free_skill_choice', 'stat', 'contact', 'ally', 'rival', 'enemy',
    'injury', 'injury_severity_choice', 'extra_benefit', 'forfeit_benefit', 'dm_benefit',
    'dm_advancement', 'dm_permanent_advancement', 'dm_survival', 'dm_qualification_terms_in_career',
    'auto_advance', 'career_continues', 'force_next_career', 'force_career_end',
    'contacts_soc_dm_min1', 'trigger_disaster_mishap', 'skill_loss_choice',
    'pending_choice', 'skill_check', 'd6_result', 'auto_qualify_careers',
    'on_nat2', 'on_pass', 'on_fail',  # these are keys, not types
    'psi_check', 'psi_training',
}

# Find all "type": "..." values
all_types = re.findall(r'"type":\s*"([^"]+)"', content)
type_counts = {}
for t in all_types:
    type_counts[t] = type_counts.get(t, 0) + 1

print("Effect type counts:")
for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    marker = "" if t in KNOWN_EFFECT_TYPES else "  <<< UNKNOWN"
    print(f"  {t}: {c}{marker}")

# Check dm_advancement with 0 amount
zero_dm = re.findall(r'"type":\s*"dm_advancement",\s*"amount":\s*0', content)
print(f"\ndm_advancement with amount=0: {len(zero_dm)}")

# Check stat effects with suspicious amounts
large_stat = re.findall(r'"type":\s*"stat",\s*"stat":\s*"(\w+)",\s*"amount":\s*(-?\d+)', content)
for stat, amt in large_stat:
    if abs(int(amt)) > 3:
        print(f"  LARGE STAT EFFECT: {stat} {amt}")
