"""Build audited historical snapshots from downloaded publisher tables."""
import ast
import json
import re
import unicodedata
from pathlib import Path
from datasets import validate, write_json

ROOT = Path(__file__).absolute().parent.parent
base = json.loads((ROOT/'dist/data/rankings-2026.json').read_text(encoding='utf-8'))
parsed = json.loads((ROOT/'research/history/parsed.json').read_text(encoding='utf-8'))
node = next(n for n in ast.parse((ROOT/'scripts/build_data.py').read_text(encoding='utf-8')).body if isinstance(n, ast.FunctionDef) and n.name == 'key')
exec(compile(ast.Module(body=[node], type_ignores=[]), 'identity rules', 'exec'))
known = {s['id']: s for s in base['schools']}
urls = {r['url']: s['id'] for s in base['schools'] for r in s['rankings'].values() if r and r.get('url')}
# Explicit publisher IDs for schools absent from the 2026 snapshot.
aliases = {'3539':'iii-dorosli','3458':'prywatne-zaoczne-dorosli','4796':'ix-dorosli','3779':'eduvision-dorosli','5134':'uczen','19361':'uczen','5088':'wolna-szkola','19341':'wolna-szkola'}
def identity(row):
    if row['url'] in urls: return urls[row['url']]
    for publisher_id, school_id in aliases.items():
        if re.search(r'(?:/|-)'+publisher_id+r'(?:/|$)', row['url'] or ''): return school_id
    school_id = key(row['name'])
    if school_id not in known: raise ValueError('Unreviewed identity: '+row['name'])
    return school_id

datasets = []
audit = []
for year in range(2017,2026):
    entries = [p for p in parsed if p['year']==year]
    schools = {}
    sources = {}
    exam = next((p['examYear'] for p in entries if p['source']=='oto'), None)
    for p in entries:
        source = p['source']
        sources[source] = dict(name='WaszaEdukacja' if source=='wasza' else 'otouczelnie', scope='w Krakowie', url=p['url'], digits=3 if source=='wasza' else 2,
            description=f"Archiwalna edycja {year}: {len(p['rows'])} opublikowanych pozycji. Zachowano miejsca i punkty wydawcy. Metodologia i liczba uwzględnionych szkół mogą różnić się między latami." + (f" Wyniki matury {exam}; punkty = 0,5 × zdawalność + polski + matematyka + angielski." if source=='oto' else ' Rok wyników egzaminacyjnych nie został potwierdzony.'))
        seen = set()
        for row in p['rows']:
            school_id = identity(row)
            if school_id in seen: raise ValueError(f'Duplicate school {source} {year} {school_id}')
            seen.add(school_id)
            if school_id not in schools:
                latest = known.get(school_id, {})
                schools[school_id] = dict(id=school_id,name=row['name'],address=latest.get('address',''),coords=latest.get('coords'),type=latest.get('type','Brak danych'),adult=latest.get('adult','doros' in row['name'].lower()),examYear=exam,profileYear='Brak historycznej oferty',profileSource='',profiles=[],tags=[],rankings={},metadataAsOf=base['updated'] if latest else None)
            schools[school_id]['rankings'][source] = dict(row, sourceUrl=p['url'])
        audit.append({k:p[k] for k in ('source','year','url','finalUrl','downloaded','sha256')} | {'rows':len(p['rows'])})
    data = dict(schemaVersion=1,rankingYear=year,examYear=exam,updated='2026-10-09',historical=True,sources=sources,schools=list(schools.values()))
    datasets.append(validate(data))
folder = ROOT/'imports'
folder.mkdir(exist_ok=True)
write_json(folder/'historical-batch.json',dict(schemaVersion=1,datasets=datasets))
write_json(folder/'history-audit.json',dict(downloaded='2026-10-09',sources=audit,notes='Adresy i współrzędne pochodzą z migawki 2026, nie są potwierdzeniem historycznej lokalizacji. Profile historyczne pozostawiono puste.'))
print('Built',len(datasets),'years;',sum(a['rows'] for a in audit),'rank records')
