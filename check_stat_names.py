"""
Check that all stat names used in {"type": "stat", "stat": "..."} effects
are valid.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find all stat names in stat effects
stat_names = set(re.findall(r'"type":\s*"stat",\s*"stat":\s*"([^"]+)"', content))
print(f"Unique stat names in stat effects: {sorted(stat_names)}")

# Valid core stats
VALID_STATS = {
    'STR', 'DEX', 'END', 'INT', 'EDU', 'SOC',
    'PSI',  # Zhodani
    'RES',  # Hiver
    'REP',  # Vargr reputation
    'TER',  # Glorious Empire Aslan
    'LCK',  # Lucky (if used)
    'CHA',  # Charisma (if used)
    'INF',  # Influence (if used)
}

unknown_stats = stat_names - VALID_STATS
if unknown_stats:
    print(f"\nUnknown stat names: {unknown_stats}")
    for stat in unknown_stats:
        # Find context
        m = re.search(rf'"stat":\s*"{re.escape(stat)}"', content)
        if m:
            lineno = content[:m.start()].count('\n') + 1
            ctx = content[max(0, m.start()-50):m.start()+80].replace('\n', ' ')
            print(f"  Line ~{lineno}: {ctx}")
else:
    print("\nAll stat names are valid!")
