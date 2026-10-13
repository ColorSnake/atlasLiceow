"""Extract ranked facts without assuming historical table layouts."""
from pathlib import Path
import re,json,html,sys
from urllib.parse import urljoin
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).absolute().parent.parent
CACHE=ROOT/'research/history'
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',s))).strip()
def link(s,base):
 m=re.search(r'href=[\"\x27]([^\"\x27]+)',s)
 return urljoin(base,html.unescape(m[1])) if m else None
def number(s):return float(s.replace(',','.').replace('%','').replace('pkt','').strip())
def parse_oto(raw,url,year):
 rows=[]
 for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',raw,re.S):
  cells=re.findall(r'<td\b[^>]*>(.*?)</td>',row,re.S)
  if len(cells)==7 and 'table-href' in cells[1]:
   vals=[clean(c) for c in cells]
   rows.append(dict(rank=int(vals[0]),name=vals[1],url=link(cells[1],url),passRate=number(vals[2]),polish=number(vals[3]),math=number(vals[4]),english=number(vals[5]),score=number(vals[6])))
 text=clean(raw)
 m=re.search(r'Wybrane kryteria rankingu\s*-\s*wyniki matury (\d{4})',text)
 if not m:raise ValueError(f'No exam year: {year}')
 expected=re.search(r'Liczba szkół spełniających kryteria:\s*(\d+)',text)
 if not expected or len(rows)!=int(expected[1]):raise ValueError(f'Incomplete oto {year}: {len(rows)} vs {expected}')
 assert f'Ranking liceów w Krakowie {year}' in text
 return rows,int(m[1])
def parse_wasza(raw,url,year):
 title=clean(re.search(r'<title>(.*?)</title>',raw,re.S)[1])
 if not re.search(r'\b'+str(year)+r'\b',title):raise ValueError(f'Wrong archive year: {title}')
 table=re.search(r'<table[^>]*id=["\x27]tabela_rankingu["\x27][^>]*>(.*?)</table>',raw,re.S)
 if not table:raise ValueError(f'Missing ranking table: {year}')
 raw=table[1]
 rows=[]
 for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',raw,re.S):
  cells=re.findall(r'<td\b[^>]*>(.*?)</td>',row,re.S)
  vals=[clean(c) for c in cells]
  if len(cells) in (3,4) and re.fullmatch(r'\d+',vals[0]) and 'pkt' in vals[-1]:
   rows.append(dict(rank=int(vals[0]),national=int(vals[1]) if len(cells)==4 else None,name=vals[-2],url=link(cells[-2],url),score=number(vals[-1])))
 text=clean(raw)
 if not rows or rows[0]['rank']!=1:raise ValueError(f'Empty or incomplete archive: {year}')
 return rows,None
if __name__=='__main__':
 output=[]
 for meta in json.loads((CACHE/'downloads.json').read_text(encoding='utf-8')):
  raw=(CACHE/meta['cache']).read_text(encoding='utf-8')
  title=clean(re.search(r'<title>(.*?)</title>',raw,re.S)[1])
  rows,exam=(parse_oto if meta['source']=='oto' else parse_wasza)(raw,meta['url'],meta['year'])
  print(meta['source'],meta['year'],'rows',len(rows),'exam',exam,'title',title)
  print('head',rows[:2]);print('tail',rows[-1:])
  output.append(dict(**meta,examYear=exam,rows=rows,title=title))
 (CACHE/'parsed.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
