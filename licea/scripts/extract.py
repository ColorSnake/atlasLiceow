"""Extract factual ranking data from cached publisher pages (Python stdlib)."""
import pathlib,re,html,json,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=pathlib.Path('licea')
def clean(s): return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s))).strip()
def read(k): return (ROOT/'research'/f'{k}.html').read_text(encoding='utf-8')
def link(s):
 m=re.search(r'href=[\"\x27]([^\"\x27]+)',s)
 return html.unescape(m[1]) if m else None
oto=[]
for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',read('oto'),re.S):
 cells=re.findall(r'<td\b[^>]*>(.*?)</td>',row,re.S)
 if len(cells)==7 and 'table-href' in cells[1]:
  vals=[clean(x) for x in cells]
  oto.append(dict(rank=int(vals[0]),name=vals[1],url=link(cells[1]),passRate=float(vals[2].strip('%')),polish=float(vals[3].strip('%')),math=float(vals[4].strip('%')),english=float(vals[5].strip('%')),score=float(vals[6])))
wasza=[]
for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',read('wasza'),re.S):
 cells=re.findall(r'<td\b[^>]*>(.*?)</td>',row,re.S)
 if len(cells)==4 and re.fullmatch(r'\d+',clean(cells[0])) and 'pkt' in cells[3]:
  vals=[clean(x) for x in cells]
  wasza.append(dict(rank=int(vals[0]),national=int(vals[1]),name=vals[2],url='https://waszaedukacja.pl'+link(cells[2]) if link(cells[2]) else None,score=float(vals[3].split()[0])))
pers=[]
for raw in re.findall(r'props="([^"]*)"',read('perspektywy')):
 try: obj=json.loads(html.unescape(raw))
 except Exception: continue
 def walk(x):
  if isinstance(x,dict):
   if 'city' in x and x['city']==[0,'Kraków'] and 'wsk' in x:
    d={k:v[1] for k,v in x.items()}
    pers.append(dict(rank=d['place'],name=clean(d['name']),url=link(d['name']),score=float(d['wsk']),history={y:d[y] for y in ['2023','2024','2025']},olymp=float(d['olymp']),basic=float(d['mat_exam_bas']),advanced=float(d['mat_exam_adv'])))
   else:
    for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(obj)
pers=list({p['name']:p for p in pers}.values())
data={'oto':oto,'wasza':wasza,'pers':pers}
(ROOT/'research'/'rankings.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
for k,v in data.items():
 print(k,len(v))
 for x in v: print(x.get('rank'),x['name'],x.get('score'))
