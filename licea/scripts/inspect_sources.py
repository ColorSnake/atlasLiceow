import urllib.request, pathlib, importlib.util
root = pathlib.Path(__file__).resolve().parents[1]
(root/'research').mkdir(exist_ok=True)
for module in ['requests','bs4','pypdf','fitz']:
    print(module, bool(importlib.util.find_spec(module)))
for key,url in [('oto','https://www.otouczelnie.pl/ranking/208/Ranking-liceow-w-Krakowie-2026'),('perspektywy','https://licea.perspektywy.pl/rankingi/ranking-glowny-liceow/'),('wasza','https://waszaedukacja.pl/ranking/krakow/licea'),('school','https://www.otouczelnie.pl/artykul/208/Licea-publiczne-i-prywatne-w-Krakowie-wyszukiwarka/292/V-LO-im-Augusta-Witkowskiego')]:
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        data=urllib.request.urlopen(req,timeout=30).read()
        (root/'research'/f'{key}.html').write_bytes(data)
        print(key,len(data))
    except Exception as e: print(key,str(e))
