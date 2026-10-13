import pathlib,json,re,sys
sys.stdout.reconfigure(encoding='utf-8')
root=pathlib.Path('licea');data=json.loads((root/'dist/data.json').read_text(encoding='utf-8'))
for s in data['schools']:
 print(s['id'],s['type'],s['coords'],len(s['profiles']),s['profileYear'],s['address'])
s=(root/'research/wasza.html').read_text(encoding='utf-8')
for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',s,re.S):
 cells=re.findall(r'<td\b[^>]*>(.*?)</td>',row,re.S)
 if len(cells)>=3 and '/ponadgimnazjalne/' not in row:print('other row',re.sub('<[^>]+>',' ',row).strip())
