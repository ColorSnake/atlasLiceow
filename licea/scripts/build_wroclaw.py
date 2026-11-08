"""Rebuild reviewed Wroclaw 2026 data from cached publisher HTML.

Run from any directory. --fetch downloads missing public pages; cached HTML is
never overwritten implicitly. No fuzzy identity matching or geocoding is used.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin

ROOT = Path(__file__).absolute().parent.parent
CACHE = ROOT / 'research' / 'wroclaw'
URLS = {
    'oto':'https://www.otouczelnie.pl/ranking/210/Ranking-liceow-we-Wroclawiu-2026',
    'wasza':'https://waszaedukacja.pl/ranking/wroclaw/licea',
    'pers':'https://licea.perspektywy.pl/rankingi/ranking-glowny-liceow/',
}
OFFICIAL_URLS = {
    'official-foundation.html':'https://geoportal.wroclaw.pl/poi/poi/24276',
    'official-music.html':'https://www.gov.pl/web/osmwroclaw/dane-kontaktowe',
}
SUPPLEMENTAL_URLS = {
    'pers-primary-2026.pdf':'https://licea.perspektywy.pl/pdf/ranking-licea-2026.pdf',
    'official-pwr-history.html':'https://liceum.pwr.edu.pl/alo/sukcesy/wyniki-szkoly/',
    'city-pers-article.html':'https://www.wroclaw.pl/dla-mieszkanca/ranking-perspektyw-2026-najlepsze-licea-i-technika-we-wroclawiu',
}
SOURCE_CHECK_NOTES = [
    'ALOPWr history 2025=11, 2024=18, 2023=9 is confirmed by the primary Perspektywy 2026 PDF (columns 2025/2024/2023) and the official school results page. The city article dated 2026-01-14 incorrectly says its 2025 place was 8; that statement was not used.',
    'III LO has score 73.42 and olympiad indicator 19.23 in the cached current publisher HTML, versus 73.36 and 19.00 in the primary 2026 PDF. Place 18= and history 2025=8, 2024=6, 2023=6 agree. This snapshot uses the HTML values fetched on 2026-11-08; PDF values are not mixed into the record.',
]
FETCHED = '2026-11-08'

def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]*>', ' ', value))).strip()

def href(value):
    match = re.search(r'href=["\x27]([^"\x27]+)', value)
    return html.unescape(match[1]) if match else None

def rows(raw):
    return [re.findall(r'<td\b[^>]*>(.*?)</td>', row, re.S) for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>', raw, re.S)]

def download(item):
    filename, url = item
    destination = CACHE / filename
    if not destination.exists():
        if datetime.now(timezone.utc).date().isoformat() != FETCHED:
            raise RuntimeError(
                f'This extractor is frozen to the {FETCHED} snapshot. Missing cache: {filename}. '
                'Do not label newer publisher pages with the old date. Prepare a new reviewed '
                'snapshot and audit with its actual fetch date, or restore the original cached HTML.'
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix('.download')
        subprocess.run(['curl.exe' if sys.platform == 'win32' else 'curl', '--fail', '--silent', '--show-error', '--retry', '2', '--max-time', '40', '--output', str(temporary), url], check=True)
        temporary.replace(destination)
    return filename, url

def parse_oto(raw):
    result = []
    assert 'wyniki matury 2025' in clean(raw)
    for cells in rows(raw):
        if len(cells) != 7 or not re.fullmatch(r'\d+', clean(cells[0])):
            continue
        values = [clean(cell) for cell in cells]
        item = dict(rank=int(values[0]),name=values[1],url=href(cells[1]),sourceUrl=URLS['oto'])
        for key, value in zip(['passRate','polish','math','english','score'], values[2:]):
            item[key] = float(value.strip('%').replace(',', '.')) if value not in ['-', '—', ''] else None
        assert all(item[key] is None or 0 <= item[key] <= 100 for key in ['passRate','polish','math','english'])
        assert abs(item['score'] - sum(item[k] for k in ['polish','math','english']) - item['passRate']/2) <= .02
        result.append(item)
    assert len(result) == 43
    return result

def parse_wasza(raw):
    result = []
    for cells in rows(raw):
        if len(cells) != 11 or not re.fullmatch(r'\d+\.', clean(cells[0])):
            continue
        name_match = re.search(r'<(?:a|span)[^>]*class="[^"]*(?:school-name|nazwa)[^"]*"[^>]*>(.*?)</(?:a|span)>', cells[1], re.S)
        anchor = re.search(r'<a\b[^>]*href="/ponadgimnazjalne/[^>]*>(.*?)</a>', cells[1], re.S)
        name = clean((name_match or anchor)[1]) if (name_match or anchor) else clean(cells[1]).split(' Wrocław')[0]
        school_url = re.search(r'href="(/ponadgimnazjalne/[^"]+)"', cells[1])
        result.append(dict(rank=int(clean(cells[0]).rstrip('.')),name=name,url=urljoin(URLS['wasza'], school_url[1]) if school_url else URLS['wasza'],sourceUrl=URLS['wasza'],score=float(clean(cells[2]).replace(',', '.')),national=int(clean(cells[7]).rstrip('.')),district=clean(cells[9]),private='niepubliczna' in clean(cells[1])))
    assert len(result) == 42
    return result

def parse_pers(raw):
    result = []
    def walk(value):
        if isinstance(value, dict):
            if value.get('city') == [0,'Wrocław'] and 'wsk' in value:
                fields = {key:item[1] for key,item in value.items()}
                result.append(dict(rank=fields['place'],name=clean(fields['name']),url=href(fields['name']),sourceUrl=URLS['pers'],score=float(fields['wsk']),history={str(year):fields[str(year)] for year in [2023,2024,2025]},olymp=float(fields['olymp']),basic=float(fields['mat_exam_bas']),advanced=float(fields['mat_exam_adv'])))
            else:
                for item in value.values(): walk(item)
        elif isinstance(value, list):
            for item in value: walk(item)
    for props in re.findall(r'props="([^"]*)"', raw):
        try: walk(json.loads(html.unescape(props)))
        except (ValueError, TypeError): pass
    result = list({item['name']:item for item in result}.values())
    assert len(result) == 23
    return result

# Explicit publisher IDs, reviewed from school names and linked cards. The two
# Ala schools and the adult LO nr I are deliberately separate identities.
OTO_IDENTITIES = {
 '4846':'akademickie-pwr', '351':'iii-lo', '353':'v-lo', '359':'xii-lo',
 '361':'xiv-lo', '357':'ix-lo', '360':'xiii-lo', '356':'viii-lo', '3067':'xvi-lo',
 '354':'vi-lo', '355':'vii-lo', '3061':'i-lo', '352':'iv-lo', '6371':'muzyczne-szymanowski',
 '358':'x-lo', '350':'ii-lo', '362':'xvii-lo', '3063':'salezjanskie', '3062':'urszulanki',
 '836':'xi-lo', '5666':'cogito', '3065':'plastyczne-kopystynski', '5297':'fundacja-jadwigi',
 '3064':'xxiv-lo', '5336':'etz-chaim', '3337':'spoleczne-ala', '3066':'xxx-lo',
 '3197':'assa', '4601':'gimbasket', '4618':'amigo', '6414':'plastyczne-ala',
 '3180':'xv-lo', '5305':'edukacja', '3954':'sms-junior', '3440':'abor', '5160':'husarz',
 '5175':'sluzb-mundurowych', '5409':'adult-magnus', '5058':'roe', '3581':'adult-i',
 '3659':'adult-zak', '3657':'adult-novum', '4021':'adult-cosinus',
}
WE_IDENTITIES = {
 '1409':'akademickie-pwr','86':'iii-lo','95':'xii-lo','89':'v-lo','286':'xiv-lo',
 '96':'xiii-lo','92':'viii-lo','18877':'urszulanki','88':'ix-lo','87':'iv-lo',
 '91':'vii-lo','84':'i-lo','98':'xvi-lo','94':'xi-lo','93':'x-lo',
 '18880':'salezjanskie','90':'vi-lo','99':'xvii-lo','19538':'etz-chaim','102':'xxx-lo',
 '19145':'spoleczne-ala','61356':'plastyczne-kopystynski','85':'ii-lo','19509':'fundacja-jadwigi',
 '19236':'amigo','100':'xxiv-lo','19014':'abor','19453':'edukacja','18876':'gimbasket',
 '19141':'assa','97':'xv-lo','19137':'sms-junior','19381':'husarz','61233':'adult-i',
 '18881':'sluzb-mundurowych','19316':'roe',
}
WE_UNLINKED = {
 'Liceum Cogito z Oddziałami Dwujęzycznymi':'cogito',
 'Liceum dla Dorosłych Magnus':'adult-magnus',
 'Społeczne Liceum Sztuk Plastycznych Ala':'plastyczne-ala',
 'Liceum dla Dorosłych Novum':'adult-novum',
 'Liceum dla Dorosłych ŻAK':'adult-zak',
 'Zaoczne Liceum Cosinus':'adult-cosinus',
}
PERS_NAMED = {
 'Akademickie LO PWr':'akademickie-pwr', 'LO Sióstr Urszulanek Unii Rzymskiej':'urszulanki',
 'Publiczne Liceum Salezjańskie':'salezjanskie',
 'Liceum Sztuk Plastycznych im. St. Kopystyńskiego':'plastyczne-kopystynski',
 'LO Cogito':'cogito', 'Niepubliczne LO Fundacji Królowej Świętej Jadwigi':'fundacja-jadwigi',
 'Liceum Ogólnokształcące Dialogu Kultur ETZ Chaim':'etz-chaim',
}

def identity(source, item):
    if source == 'oto':
        return OTO_IDENTITIES[item['url'].split('/')[-2]]
    if source == 'wasza':
        if '/ponadgimnazjalne/' in item['url']:
            return WE_IDENTITIES[item['url'].rsplit('-', 1)[-1]]
        return WE_UNLINKED[item['name']]
    if item['name'] in PERS_NAMED:
        return PERS_NAMED[item['name']]
    match = re.fullmatch(r'LO nr ([IVXL]+)(?: im\..*)?', item['name'])
    if not match: raise ValueError('Unreviewed Perspektywy school identity: ' + item['name'])
    return match[1].lower() + '-lo'

def card_metadata(page, source):
    result = dict(address='', coords=None, website=None, profiles=[], profileYear='Rok oferty niepotwierdzony', type='Brak danych')
    if source == 'wasza':
        for value in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', page, re.S):
            try: record = json.loads(value)
            except ValueError: continue
            if not isinstance(record, dict) or not isinstance(record.get('address'), dict): continue
            address = record['address']
            if address.get('addressLocality') != 'Wrocław': continue
            result['address'] = address.get('streetAddress', '') + ', Wrocław'
            geo = record.get('geo', {})
            if geo.get('latitude') is not None and geo.get('longitude') is not None:
                coords = [float(geo['latitude']), float(geo['longitude'])]
                if 51 < coords[0] < 51.25 and 16.8 < coords[1] < 17.25: result['coords'] = coords
            result['website'] = record.get('sameAs')
        kind = re.search(r'<dt>Rodzaj</dt>\s*<dd>(.*?)</dd>', page, re.S)
        if kind:
            text = clean(kind[1])
            result['type'] = 'Niepubliczna' if 'niepublicz' in text else 'Publiczna' if 'publicz' in text else 'Brak danych'
        table = re.search(r'<table class="pp-klasy-skrot">(.*?)</table>', page, re.S)
        year = re.search(r'Klasy (20\d{2}/20\d{2})', page)
        if table and year:
            for cells in rows(table[1]):
                if len(cells) >= 2:
                    result['profiles'].append(clean(cells[0]) + ' / ' + clean(cells[1]))
            result['profileYear'] = year[1]
    else:
        address = re.search(r'<div class="address_row"[^>]*>(.*?)</div>', page, re.S)
        if address:
            text = clean(address[1])
            match = re.match(r'(.*?Wrocław)', text)
            if match: result['address'] = re.sub(r'\s*\d{2}-\d{3}\s*', ', ', match[1])
    return result

def assemble(parsed):
    schools = {}
    for source, records in parsed.items():
        for index, record in enumerate(records):
            school_id = identity(source, record)
            if school_id not in schools:
                schools[school_id] = dict(id='wroclaw-'+school_id,name=re.sub(r'\s+(?:we?|We) Wrocławiu$', '', record['name']),address='',district='',type='Brak danych',adult=school_id.startswith('adult-'),coords=None,coordSource=None,addressSource=None,website=None,examYear=2025,profiles=[],profileYear='Rok oferty niepotwierdzony',profileSource='',tags=[],rankings={})
            school = schools[school_id]
            assert source not in school['rankings'], (source, school_id)
            school['rankings'][source] = {key:value for key,value in record.items() if key not in ['district','private']}
            if source == 'pers':
                if not school['website']: school['website'] = record['url']
                continue
            path = CACHE / f'{source}-{index}.html'
            if source == 'wasza':
                school['name'] = record['name']
                school['district'] = record['district']
                if record['private']: school['type'] = 'Niepubliczna'
                if '/ponadgimnazjalne/' not in record['url']: continue
            metadata = card_metadata(path.read_text(encoding='utf-8'), source)
            for key in ['address','coords','website','profiles']:
                if metadata[key]:
                    school[key] = metadata[key]
                    if key == 'address': school['addressSource'] = record['url']
                    elif key == 'coords': school['coordSource'] = record['url']
                    elif key == 'profiles':
                        school['profileSource'] = record['url'] + '/profile'
                        school['profileYear'] = metadata['profileYear']
            if metadata['type'] != 'Brak danych': school['type'] = metadata['type']
    # Published WE coordinates do not match the address Robotnicza 36-38.
    # The municipal POI and official school statute confirm the street address,
    # but do not provide a directly verified WGS84 point in this extraction.
    foundation = schools['fundacja-jadwigi']
    foundation['coords'] = None
    foundation['coordSource'] = None
    foundation['addressSource'] = 'https://geoportal.wroclaw.pl/poi/poi/24276'
    foundation['district'] = 'Fabryczna'
    music = schools['muzyczne-szymanowski']
    music['addressSource'] = 'https://www.gov.pl/web/osmwroclaw/dane-kontaktowe'
    music['website'] = 'https://www.gov.pl/web/osmwroclaw'
    for school in schools.values():
        names = ' '.join(school['profiles']).lower()
        for pattern, label in [(r'matem|fiz|informat','Ścisłe'),(r'biol|chem','Biol-chem'),(r'polsk|hist|wos|human|praw','Humanistyczne'),(r'geogr|ekonom|biznes','Geograficzne'),(r'dwuj|język|angiel|niemie|hiszp|franc','Językowe'),(r'sport','Sportowe'),(r'artyst|muzy|plast','Artystyczne')]:
            if re.search(pattern,names): school['tags'].append(label)
    sources = {
        'wasza':dict(name='WaszaEdukacja',url=URLS['wasza'],scope='we Wrocławiu',digits=2,description='Ranking liceów 2026, migawka pobrana 08.11.2026: 42 szkoły, oryginalne miejsca we Wrocławiu i punkty wydawcy. Obecna metodologia uwzględnia matury, olimpiady i EWD. Punkty nie są bezpośrednio porównywalne z innymi wydawcami ani starszymi migawkami metodologii. Wyników matury 2026 z kart WaszaEdukacja nie połączono z maturą 2025 z otouczelnie.'),
        'oto':dict(name='otouczelnie',url=URLS['oto'],scope='we Wrocławiu',digits=2,description='Ranking liceów we Wrocławiu 2026 obejmuje 43 szkoły; dane egzaminacyjne dotyczą matury 2025: terminu głównego, dodatkowego i poprawkowego. Wydawca wymaga co najmniej 10 zdających i co najmniej 10% zdawalności. Punkty = 0,5 × zdawalność + polski + matematyka + angielski (podstawa). Zdawalność jest podana dla każdej szkoły; nie jest średnią wyników przedmiotowych.'),
        'pers':dict(name='Perspektywy',url=URLS['pers'],scope='w Polsce',digits=2,description='Ogólnopolski Ranking Liceów Perspektywy 2026: 23 szkoły z Wrocławia. Zachowano oryginalne miejsca krajowe i ex aequo, bez tworzenia rankingu miejskiego. Historia 2023–2025 pochodzi z tabeli historii wydania 2026. Metodologia: 25% olimpiady, 30% matura obowiązkowa, 45% matura dodatkowa; nie obejmuje matury IB.'),
    }
    return dict(schemaVersion=1,city='wroclaw',schoolType='liceum',rankingYear=2026,examYear=2025,updated=FETCHED,sources=sources,schools=list(schools.values()))

def publish(parsed, details):
    data = assemble(parsed)
    assert len(data['schools']) == 43
    assert len({school['id'] for school in data['schools']}) == 43
    for school in data['schools']:
        assert school['rankings']['oto']['passRate'] is not None
    output = ROOT/'public/atlas/data/wroclaw/rankings-2026.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    audit_files = [(source+'.html',url) for source,url in URLS.items()] + details
    audit_files += list(OFFICIAL_URLS.items())
    audit = dict(schemaVersion=1,city='wroclaw',rankingYear=2026,examYear=2025,fetched=FETCHED,counts=dict(schools=len(data['schools']),mapped=sum(bool(s['coords']) for s in data['schools']),profiles=sum(bool(s['profiles']) for s in data['schools']),sources={k:len(v) for k,v in parsed.items()},passRates=sum(s['rankings']['oto'].get('passRate') is not None for s in data['schools'])),identityRules='Explicit publisher ID/name maps in scripts/build_wroclaw.py; no fuzzy matching. The two Ala schools, public LO I and adult LO I are separate.',limitations=['Only edition 2026 is imported for Wrocław. Perspektywy historical positions 2023–2025 remain publisher history, not independently imported snapshots.','Missing and conflicting coordinates remain null; no guessed markers or automatic geocoding.','WE foundation school coordinates 51.120058,17.037126 rejected because they do not match Robotnicza 36-38 confirmed by municipal POI.','Published address and coordinates describe the source snapshot, not guaranteed historical locations or entrance positions.','WaszaEdukacja cards show matura2026; displayed examination percentages and pass rates in this dataset exclusively use OTO matura2025.','The OTO label Spoleczne Liceum Ogolnoksztalcace is identified as Ala by the linked school card title; art-school Ala is a distinct row.'],missingCoordinates=[dict(id=s['id'],name=s['name'],address=s['address']) for s in data['schools'] if not s['coords']],pages=[dict(file=filename,url=url,fetched=FETCHED,sha256=hashlib.sha256((CACHE/filename).read_bytes()).hexdigest()) for filename,url in audit_files])
    audit['limitations'].extend(SOURCE_CHECK_NOTES)
    audit['supplementalSources'] = [dict(file=filename,url=url,fetched=FETCHED,sha256=hashlib.sha256((CACHE/filename).read_bytes()).hexdigest()) for filename,url in SUPPLEMENTAL_URLS.items()]
    (ROOT/'imports/wroclaw-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit['counts'],ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Download missing public HTML into ignored research cache.')
    parser.add_argument('--inspect', action='store_true', help='Save parsed records and inspect detail pages without publishing data.')
    args = parser.parse_args()
    if args.fetch:
        for source, url in URLS.items(): download((source + '.html', url))
        for filename, url in OFFICIAL_URLS.items(): download((filename, url))
        for filename, url in SUPPLEMENTAL_URLS.items(): download((filename, url))
    parsed = {key:globals()['parse_' + key]((CACHE/(key+'.html')).read_text(encoding='utf-8')) for key in URLS}
    (CACHE/'parsed.json').write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding='utf-8')
    details = [(f'oto-{index}.html', item['url']) for index,item in enumerate(parsed['oto'])]
    details += [(f'wasza-{index}.html', item['url']) for index,item in enumerate(parsed['wasza']) if '/ponadgimnazjalne/' in item['url']]
    if args.fetch:
        with ThreadPoolExecutor(max_workers=4) as executor: list(executor.map(download, details))
    print({key:len(value) for key,value in parsed.items()})
    if args.inspect:
        for source in ['oto','wasza']:
            page=(CACHE/f'{source}-0.html').read_text(encoding='utf-8')
            for token in ['address_row','itemprop="address"','tc=','Rodzaj:','profil','latitude','longitude']:
                index=page.find(token)
                if index>=0: print(source,token,page[max(0,index-100):index+350])
    else:
        publish(parsed, details)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
