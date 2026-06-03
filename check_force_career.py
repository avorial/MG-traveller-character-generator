"""
Check all force_next_career effects point to valid career IDs.
"""
import re, os

with open('app/engine/lifepath.py', encoding='utf-8') as f:
    content = f.read()

# Get all career JSON IDs
career_dir = 'app/data/careers'
career_ids = {os.path.splitext(f)[0] for f in os.listdir(career_dir) if f.endswith('.json')}

# Find all force_next_career career_id values
forced = re.findall(r'"type":\s*"force_next_career",\s*"career_id":\s*"([^"]+)"', content)
print(f"force_next_career entries: {len(forced)}")

invalid = []
for career_id in forced:
    if career_id not in career_ids:
        invalid.append(career_id)

if invalid:
    print("INVALID career IDs:")
    for c in invalid:
        print(f"  {c}")
else:
    print("All force_next_career IDs are valid career IDs!")
