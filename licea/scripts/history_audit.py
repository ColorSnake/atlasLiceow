import ast,json,re,sys,unicodedata
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
root=Path('licea');parsed=json.loads((root/'research/history/parsed.json').read_text(encoding='utf-8'));base=json.loads((root/'public/atlas/data/rankings-2026.json').read_text(encoding='utf-8'))
# Read the existing identity rules without executing the legacy data builder.
node=next(n for n in ast.parse((root/'scripts/build_data.py').read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='key')
exec(compile(ast.Module(body=[node],type_ignores=[]),'identity rules','exec'))
ids={s['id']:s for s in base['schools']}
urlids={r['url']:s['id'] for s in base['schools'] for r in s['rankings'].values() if r and r.get('url')}
unknown={};rows=[]
for p in parsed:
 seen={}
 for row in p['rows']:
  k=urlids.get(row['url']) or key(row['name'])
  if k not in ids:unknown.setdefault(k,set()).add((p['source'],row['name'],row['url']))
  if k in seen:print('DUPLICATE',p['source'],p['year'],k,seen[k],row)
  seen[k]=row
  rows.append(dict(year=p['year'],source=p['source'],id=k,name=row['name'],url=row['url']))
for k,v in unknown.items():print('UNMAPPED',k,list(v))
(root/'research/history/matches.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
for y in [2017,2018,2019,2020,2021]:
 raw=(root/f'research/history/wasza-{y}.html').read_text(encoding='utf-8')
 print('YEAR',y)
 for pat in ['metodolog','caly_ranking','tabela_rankingu','rankingu znalaz']:
  hits=list(re.finditer(pat,raw,re.I))
  for m in hits[-2:]:print(pat,raw[max(0,m.start()-100):m.start()+500])
