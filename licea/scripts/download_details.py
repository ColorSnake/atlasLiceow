import pathlib,json,urllib.request,concurrent.futures,sys
sys.stdout.reconfigure(encoding='utf-8')
root=pathlib.Path('licea/research'); data=json.loads((root/'rankings.json').read_text(encoding='utf-8'))
def fetch(job):
 key,url=job; dest=root/(key+'.html')
 if dest.exists():return key,'cached'
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  dest.write_bytes(urllib.request.urlopen(req,timeout=30).read())
  return key,'ok'
 except Exception as e:return key,str(e)
jobs=[('oto-'+str(i),s['url']) for i,s in enumerate(data['oto'])]
jobs += [('wasza-'+str(i),s['url']) for i,s in enumerate([x for x in data['wasza'] if x['url']])]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 results=list(ex.map(fetch,jobs))
print('downloaded',len(results),'errors',[r for r in results if r[1] not in ['ok','cached']])
