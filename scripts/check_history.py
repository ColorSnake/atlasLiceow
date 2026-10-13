import json
import hashlib
import subprocess
from pathlib import Path
from build_history import identity
root=Path(__file__).absolute().parent.parent
parsed=json.loads((root/'research/history/parsed.json').read_text(encoding='utf-8'))
for p in parsed:
    data=json.loads((root/f'public/atlas/data/rankings-{p["year"]}.json').read_text(encoding='utf-8'))
    lookup={s['id']:s for s in data['schools']}
    assert len([s for s in data['schools'] if s['rankings'].get(p['source'])])==len(p['rows'])
    for row in p['rows']:
        saved=lookup[identity(row)]['rankings'][p['source']]
        assert all(saved[k]==v for k,v in row.items())
        if p['source']=='oto':assert abs(row['score']-(row['passRate']/2+row['polish']+row['math']+row['english']))<.011
    print(p['source'],p['year'],len(p['rows']),p['title'].encode('ascii','replace').decode())
before=subprocess.check_output(['git','show','8a3751698fc9054f6f529fd60864756bc374df52:dist/data/rankings-2026.json'],cwd=root)
assert hashlib.sha256(before).digest()==hashlib.sha256((root/'public/atlas/data/rankings-2026.json').read_bytes()).digest()
print('All 667 original records preserved; 2026 unchanged.')
