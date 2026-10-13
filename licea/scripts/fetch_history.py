"""Download public annual ranking pages, keeping raw cache and hashes."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).absolute().parent.parent
CACHE=ROOT/'research/history'
CACHE.mkdir(parents=True,exist_ok=True)
jobs=[('oto',y,f'https://www.otouczelnie.pl/ranking/208/Ranking-liceow-w-Krakowie-{y}') for y in range(2022,2026)]
jobs += [('wasza',y,f'https://waszaedukacja.pl/ranking/krakow/licea/{y}') for y in range(2017,2026)]
def fetch(job):
 source,year,url=job
 path=CACHE/f'{source}-{year}.html'
 if path.exists():
  raw=path.read_bytes();final=url
 else:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=45) as response:
   raw=response.read();final=response.url
  path.write_bytes(raw)
 return dict(source=source,year=year,url=url,finalUrl=final,downloaded='2026-10-09',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),cache=path.name)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 results=list(pool.map(fetch,jobs))
(CACHE/'downloads.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
for result in results:print(result['source'],result['year'],result['bytes'],result['finalUrl'])
