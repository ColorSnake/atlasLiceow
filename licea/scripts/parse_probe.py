import pathlib,re,html,json,sys
sys.stdout.reconfigure(encoding='utf-8')
root=pathlib.Path('licea/research')
for key,patterns in {'school':['Studencka','Przedmioty rozszerzone','maps','latitude','profil-style'],'oto':['322.71'],'wasza':['69.758','tabela_rankingu'],'perspektywy':['Witkowskiego']}.items():
 s=(root/f'{key}.html').read_text(encoding='utf-8')
 for pattern in patterns:
  m=re.search(pattern,s)
  print(key,pattern,s[max(0,m.start()-500):m.start()+1000] if m else 'missing')
