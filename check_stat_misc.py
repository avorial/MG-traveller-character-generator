"""
Check stat_cap effects use valid stat names and caps.
Also check d_stat effects.
Also check dm_benefit vs dm_advancement usage patterns.
"""
import re

with open('app/engine/lifepath.py', encoding='utf-8', errors='replace') as f:
    content = f.read()

# stat_cap
caps = re.findall(r'"type":\s*"stat_cap",\s*"stat":\s*"([^"]+)",\s*"cap":\s*(\d+)', content)
print("stat_cap entries:")
for stat, cap in caps:
    print(f"  {stat} cap {cap}")

# d_stat
dstats = re.findall(r'"type":\s*"d_stat",\s*"stat":\s*"([^"]+)",\s*"dice":\s*"([^"]+)"', content)
print(f"\nd_stat entries:")
for stat, dice in dstats:
    print(f"  {stat}, dice={dice}")

# dm_benefit usage — should only be +1 or +2
dm_benefits = re.findall(r'"type":\s*"dm_benefit",\s*"amount":\s*(-?\d+)', content)
print(f"\ndm_benefit amounts: {sorted(set(int(a) for a in dm_benefits))}")

# dm_advancement amounts — check for unusual values
dm_advances = re.findall(r'"type":\s*"dm_advancement",\s*"amount":\s*(-?\d+)', content)
unusual = {int(a) for a in dm_advances if abs(int(a)) > 4 and abs(int(a)) != 12}
if unusual:
    print(f"\nUnusual dm_advancement amounts: {unusual}")
else:
    print(f"\ndm_advancement amounts: {sorted(set(int(a) for a in dm_advances))} — all look normal")
