import os
import re

migrations_dir = 'backend/migrations/versions'
files = [f for f in os.listdir(migrations_dir) if f.endswith('.py') and not f.startswith('__')]

rev_map = {}
down_map = {}

print("=== Scanning Migration Files ===")
for f in sorted(files):
    path = os.path.join(migrations_dir, f)
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    
    rev_match = re.search(r"revision:\s*str\s*=\s*['\"]([^'\"]+)['\"]", content)
    down_match = re.search(r"down_revision:\s*Union\[[^\]]+\]\s*=\s*(['\"][^'\"]+['\"]|None)", content)
    
    if not rev_match:
        print(f"ERROR: No revision ID found in {f}")
        continue
    
    rev_id = rev_match.group(1)
    down_id_raw = down_match.group(1) if down_match else None
    down_id = down_id_raw.strip('\'"') if (down_id_raw and down_id_raw != 'None') else None
    
    print(f"File: {f}")
    print(f"  Revision ID:   {rev_id} (length: {len(rev_id)})")
    print(f"  Down Revision: {down_id}")
    
    assert len(rev_id) <= 32, f"Revision ID {rev_id} exceeds 32 chars: {len(rev_id)}"
    assert rev_id not in rev_map, f"Duplicate revision ID {rev_id}"
    
    rev_map[rev_id] = f
    down_map[rev_id] = down_id

print("\n=== Resolving Down Revisions ===")
all_revs = set(rev_map.keys())
for rev, down in down_map.items():
    if down is not None:
        assert down in all_revs, f"down_revision {down} does not resolve!"
        print(f"  OK: {rev} -> {down}")
    else:
        print(f"  OK: {rev} (root)")

# Check heads
heads = [r for r in all_revs if r not in down_map.values()]
print(f"\n=== Heads ({len(heads)}) ===")
for h in heads:
    print(f"  Head: {h}")

assert len(heads) == 1, f"Expected exactly 1 head, got {len(heads)}"
print("\n>>> STATIC CONSISTENCY CHECK: ALL 4 CHECKS PASSED SUCCESSFULLY! <<<")
