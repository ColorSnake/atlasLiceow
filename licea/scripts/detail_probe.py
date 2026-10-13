import pathlib,re,sys
sys.stdout.reconfigure(encoding='utf-8')
root=pathlib.Path('licea/research')
s=(root/'wasza-0.html').read_text(encoding='utf-8')
for pattern in ['<a class="profil"','<div class="address_row"','Rodzaj:']:
 m=re.search(pattern,s,re.I)
 print(pattern, s[max(0,m.start()-50):m.start()+1800] if m else 'missing')
for k in []:
 s=(root/(k+'.html')).read_text(encoding='utf-8')
 print(k, 'external links',re.findall(r'href="(https?://[^"]+)"',s)[-40:])
