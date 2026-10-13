from pathlib import Path
import json
root=Path(__file__).absolute().parent.parent
data={str(d['rankingYear']):d for p in sorted((root/'public/atlas/data').glob('rankings-*.json')) for d in [json.loads(p.read_text(encoding='utf-8'))]}
(root/'server/seed.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
