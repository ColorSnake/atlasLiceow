"""Join publisher records using explicit school identities; never fuzzy-match silently."""
import pathlib,json,re,html,sys,unicodedata
sys.stdout.reconfigure(encoding='utf-8')
ROOT=pathlib.Path('licea'); R=ROOT/'research'; D=ROOT/'dist';D.mkdir(exist_ok=True)
data=json.loads((R/'rankings.json').read_text(encoding='utf-8'))
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s))).strip()
def key(name):
 n=unicodedata.normalize('NFKD',name.lower()).encode('ascii','ignore').decode()
 n=n.replace('ł','l')
 if 'doros' in n:
  for token,k in [('4u','adult-4u'),('york','adult-york'),('cosinus','adult-cosinus'),('renoma','adult-renoma'),('zakadu','adult-zdz'),('zdz','adult-zdz'),('"zak','adult-zak'),('ych zak','adult-zak'),('niepubliczne liceum','adult-zaoczne')]:
   if token in n:return k
 special=[('augustian','rita'),('rity','rita'),('salezjansk','salezjanie'),('salezjanek','salezjanki'),('pijar','pijarzy'),('michaowsk','michalowski'),('michalowsk','michalowski'),('noblist','noblisci'),('nazaret','nazaret'),('jezuit','kostka'),('prezent','prezentki'),('montessori','montessori'),('plastycz','plastyczne'),('karowicz','muzyka-karlowicz'),('karłowicz','muzyka-karlowicz'),('chopin','muzyka-chopin'),('ogolnoksztacaca szkoa muzyczna','muzyka-karlowicz'),('gortat','gortat'),('monda','mond'),('emmanuel','emmanuel'),('apostoo','apostolow'),('apostol','apostolow'),('sendzimir','sendzimir')]
 for token,k in special:
  if token in n:return k
 m=re.match(r'^([ivxl]+)\s',n)
 if m:return m[1]+('-dorosli' if 'doros' in n else '-sport' if 'sportowe' in n else '-prywatne' if 'prywatne' in n else '-spoleczne' if 'spoeczne' in n else '-lo')
 if 'spoeczne' in n and 'mistrzostwa' in n:return 'sms-spoleczne'
 if 'mistrzostwa sportowego' in n:return 'sms'
 return n
W={key(s['name']):(i,s) for i,s in enumerate(data['wasza'])}
P={key(s['name']):s for s in data['pers']}
assert len(W)==len(data['wasza']) and len(P)==len(data['pers']), 'duplicate identity'
schools=[]
for i,o in enumerate(data['oto']):
 k=key(o['name']); page=(R/f'oto-{i}.html').read_text(encoding='utf-8')
 address=re.search(r'<div class="address_row"[^>]*>(.*?)</div>',page,re.S)
 addr=clean(address[1]) if address else ''
 district=re.findall(r'<br\s*/?>([^<]+)</span>',address[1],re.S) if address else []
 district=clean(district[-1]) if district else ''
 classes=[clean(c) for c in re.findall(r'<h2>\s*(Klasa.*?)</h2>',page,re.S)]
 profileSource=o['url']; profileYear='Rok oferty niepotwierdzony'
 coords=None; coordSource=None; website=None; typ='Brak danych'
 w=None
 if k in W and W[k][1]['url']:
  j,w=W[k]
  # Cached filenames originally followed the subset of rows with school links.
  linked=[x for x in data['wasza'] if x['url']]
  j=linked.index(w);wp=(R/f'wasza-{j}.html').read_text(encoding='utf-8')
  m=re.search(r'tc=([\d.]+):([\d.]+)',wp)
  if m:coords=[float(m[1]),float(m[2])];coordSource=w['url']
  a=re.search(r'itemprop="address">(.*?)</span>',wp,re.S)
  if a:addr=clean(a[1])
  c=re.findall(r'<a class="profil"[^>]*href="/ponadgimnazjalne/[^>]+>(.*?)</a>',wp,re.S)
  if c:
   classes=[clean(x) for x in c];profileSource=w['url']+'/profile'
   y=re.search(r'Profile i punkty:.*?na rok (\d{4}/\d{4})',wp)
   if y:profileYear=y[1]
  m=re.search(r'Rodzaj:</span><span class="span_2">(.*?)</span>',wp)
  if m:typ='Niepubliczna' if 'niepubliczna' in m[1] else 'Publiczna' if 'publiczna' in m[1] else clean(m[1])
  m=re.search(r'class="strona"[^>]+href="([^"]+)"',wp)
  if m:website=html.unescape(m[1])
 if k in W:w=W[k][1]
 p=P.get(k)
 if not website and p:website=p['url']
 # Subject families are derived from the published class names, not a quality assessment.
 joined=' '.join(classes).lower();tags=[]
 for pattern,label in [(r'mat|fiz|inf','Ścisłe'),(r'biol|chem','Biol-chem'),(r'pol|hist|wos|human|praw','Humanistyczne'),(r'geo|ekonom|biznes','Geograficzne'),(r'dwuj|język|jezyk|lingw|ang|niem|hiszp|franc|\bib\b','Językowe'),(r'sport','Sportowe'),(r'artyst|muzy|plast','Artystyczne')]:
  if re.search(pattern,joined):tags.append(label)
 schools.append(dict(id=k,name=o['name'].removesuffix(' w Krakowie'),address=addr,district=district,type=typ,adult='doros' in o['name'].lower(),coords=coords,coordSource=coordSource,website=website,profiles=classes,profileSource=profileSource,profileYear=profileYear,tags=tags,rankings={'oto':o,'wasza':w,'pers':p}))
assert len(set(s['id'] for s in schools))==len(schools)
used={s['id'] for s in schools}
print('Unmatched Wasza:',[(k,v[1]['name']) for k,v in W.items() if k not in used])
print('Unmatched Perspektywy:',[(k,v['name']) for k,v in P.items() if k not in used])
print('Missing coordinates:',[(s['id'],s['address']) for s in schools if not s['coords']])
overrides=ROOT/'school_overrides.json'
if overrides.exists():
 for s in schools:
  override=json.loads(overrides.read_text(encoding='utf-8')).get(s['id'],{})
  s.update(override)
geo=R/'geocodes.json'
if geo.exists():
 for s in schools:
  g=json.loads(geo.read_text(encoding='utf-8')).get(s['id'])
  if not s['coords'] and g:s['coords']=g['coords'];s['coordSource']=g['source']
payload=dict(updated='2026-10-04',schools=schools)
(D/'data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
(D/'data.js').write_text('window.SCHOOL_DATA = '+json.dumps(payload,ensure_ascii=False)+';\n',encoding='utf-8')
print('Schools',len(schools),'mapped',sum(bool(s['coords']) for s in schools),'profiles',sum(bool(s['profiles']) for s in schools))
