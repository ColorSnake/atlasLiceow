"""Manage annual snapshots. Python 3.9+, standard library only."""
import argparse
import datetime
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).absolute().parent.parent
DIST = ROOT / 'public' / 'atlas'
CITY_REGISTRY = ROOT / 'cities.json'
DEFAULT_CITY = 'krakow'

def registered_cities():
    return {city['id']: city for city in json.loads(CITY_REGISTRY.read_text(encoding='utf-8'))['cities']}

def city_id(data):
    # Original Kraków snapshots remain byte-for-byte unchanged.
    return data.get('city', DEFAULT_CITY)

def city_directory(dist, city):
    return dist / 'data' if city == DEFAULT_CITY else dist / 'data' / city

def validate(data):
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    def year(value):
        return type(value) is int and 2000 <= value <= 2100
    def number(value):
        return type(value) in (int, float) and math.isfinite(value)
    require(isinstance(data, dict), 'Zestaw musi być obiektem JSON.')
    require(data.get('schemaVersion') == 1, 'Nieobsługiwana schemaVersion (wymagana: 1).')
    city = city_id(data)
    require(isinstance(city, str) and city in registered_cities(), 'Nieznane miasto. Dodaj je najpierw do cities.json.')
    require(data.get('schoolType', 'liceum') == 'liceum', 'Nieobsługiwany typ szkoły. Dane szkół podstawowych wymagają osobnego modelu.')
    min_lat, min_lon, max_lat, max_lon = registered_cities()[city]['bounds']
    require(year(data.get('rankingYear')), 'Nieprawidłowy rankingYear.')
    require(data.get('examYear') is None or year(data['examYear']), 'Nieprawidłowy examYear.')
    datetime.date.fromisoformat(data['updated'])
    sources = data.get('sources')
    require(isinstance(sources, dict) and bool(sources) and set(sources) <= {'oto', 'wasza', 'pers'}, 'Nieprawidłowe sources.')
    for key, src in sources.items():
        require(isinstance(src, dict), f'{key}: nieprawidłowe metadane.')
        for field in ('name', 'scope', 'url', 'description'):
            require(isinstance(src.get(field), str) and bool(src[field]), f'{key}: brak {field}.')
        require(src['url'].startswith(('https://', 'http://')), f'{key}: nieprawidłowy URL.')
        require(type(src.get('digits')) is int and 0 <= src['digits'] <= 6, f'{key}: nieprawidłowe digits.')
    schools = data.get('schools')
    require(isinstance(schools, list) and bool(schools), 'Zestaw nie zawiera szkół.')
    ids = set()
    for s in schools:
        require(isinstance(s, dict), 'Nieprawidłowa karta szkoły.')
        require(isinstance(s.get('id'), str) and bool(s['id']) and s['id'] not in ids, 'Brak lub powtórzone id szkoły.')
        ids.add(s['id'])
        for field in ('name', 'address', 'type', 'profileYear', 'profileSource'):
            require(isinstance(s.get(field), str), f'{s["id"]}: brak {field}.')
        require(bool(s['name']), 'Pusta nazwa szkoły.')
        require(type(s.get('adult')) is bool, f'{s["id"]}: brak adult.')
        for field in ('tags', 'profiles'):
            require(isinstance(s.get(field), list) and all(isinstance(x, str) for x in s[field]), f'{s["id"]}: nieprawidłowe {field}.')
        require('examYear' in s and (s['examYear'] is None or year(s['examYear'])), f'{s["id"]}: brak/nieprawidłowy examYear.')
        require(s['examYear'] == data.get('examYear') or data.get('examYear') is None, f'{s["id"]}: examYear sprzeczny z rokiem całego zestawu.')
        coords = s.get('coords')
        require(coords is None or (isinstance(coords, list) and len(coords) == 2 and all(number(c) for c in coords) and min_lat < coords[0] < max_lat and min_lon < coords[1] < max_lon), f'{s["id"]}: współrzędne poza obszarem miasta {city} lub zły format.')
        require(isinstance(s.get('rankings'), dict), f'{s["id"]}: brak rankings.')
        for key, rank in s['rankings'].items():
            if rank is None:
                continue
            require(key in sources, f'{s["id"]}: brak metadanych źródła {key}.')
            require(isinstance(rank, dict) and re.fullmatch(r'[1-9]\d*=?', str(rank.get('rank'))) is not None, f'{s["id"]}: nieprawidłowe miejsce.')
            require(number(rank.get('score')) and rank['score'] >= 0, f'{s["id"]}: nieprawidłowy wynik punktowy.')
            if key == 'oto':
                for field in ('polish', 'math', 'english', 'passRate'):
                    require(rank.get(field) is None or (number(rank[field]) and 0 <= rank[field] <= 100), f'{s["id"]}: nieprawidłowy procent {field}.')
            if key == 'pers':
                require(isinstance(rank.get('history', {}), dict), f'{s["id"]}: nieprawidłowa historia.')
                for y, position in rank.get('history', {}).items():
                    require(str(y).isdigit() and 2000 <= int(y) < data['rankingYear'], f'{s["id"]}: rok historii musi poprzedzać ranking.')
                    require(str(position) == '-' or re.fullmatch(r'[1-9]\d*=?', str(position)) is not None, f'{s["id"]}: nieprawidłowe miejsce historyczne.')
    return data

def read_snapshots(directory, city=None):
    result = {}
    for file in sorted(directory.glob('rankings-*.json')):
        data = validate(json.loads(file.read_text(encoding='utf-8')))
        if city is not None and city_id(data) != city:
            raise ValueError(f'Miasto w pliku nie odpowiada katalogowi: {file}')
        y = str(data['rankingYear'])
        if file.name != f'rankings-{y}.json' or y in result:
            raise ValueError(f'Nazwa pliku nie odpowiada rankingYear: {file.name}')
        result[y] = data
    return result

def write_json(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)

def rebuild(dist=DIST, snapshots=None, city=DEFAULT_CITY):
    cities = registered_cities()
    by_city = {key: (snapshots if key == city and snapshots is not None else read_snapshots(city_directory(dist, key), key)) for key in cities}
    by_city = {key: value for key, value in by_city.items() if value}
    if not by_city:
        raise ValueError('Brak roczników.')
    configured_default = json.loads(CITY_REGISTRY.read_text(encoding='utf-8')).get('defaultCity', DEFAULT_CITY)
    default_city = configured_default if configured_default in by_city else next(iter(by_city))
    snapshots = by_city[default_city]
    latest = max(snapshots, key=int)
    catalog = {'schemaVersion': 1, 'schoolType': 'liceum', 'defaultCity': default_city,
               'cities': [cities[key] for key in by_city], 'datasetsByCity': by_city}
    # Bundle enables direct file:// use, without fetch/CORS or a backend.
    bundle = 'window.SCHOOL_CATALOG = ' + json.dumps(catalog, ensure_ascii=False, allow_nan=False) + ';\n'
    bundle += f'window.SCHOOL_DATASETS = window.SCHOOL_CATALOG.datasetsByCity["{default_city}"];\n'
    bundle += f'window.SCHOOL_DATA = window.SCHOOL_DATASETS["{latest}"];\n'
    temporary = dist / 'data.js.tmp'
    temporary.write_text(bundle, encoding='utf-8')
    temporary.replace(dist / 'data.js')
    write_json(dist / 'data.json', snapshots[latest])
    index = {'schemaVersion': 1, 'defaultCity': default_city, 'cities': catalog['cities'], 'defaultYear': int(latest), 'years': sorted(map(int, snapshots), reverse=True)}
    write_json(dist / 'data' / 'index.json', index)
    for key, annual in by_city.items():
        if key != DEFAULT_CITY:
            write_json(city_directory(dist, key) / 'index.json', {'schemaVersion': 1, 'city': key, 'defaultYear': max(map(int, annual)), 'years': sorted(map(int, annual), reverse=True)})
    if dist == DIST and (ROOT / 'server').exists():
        write_json(ROOT / 'server' / 'seed.json', catalog)

def import_snapshot(filename, replace=False, dist=DIST):
    data = validate(json.loads(Path(filename).read_text(encoding='utf-8')))
    city = city_id(data)
    folder = city_directory(dist, city)
    snapshots = read_snapshots(folder, city)
    y = str(data['rankingYear'])
    if y in snapshots and not replace:
        raise ValueError(f'Rocznik {y} już istnieje. Użyj --replace tylko przy świadomej korekcie tego rocznika.')
    snapshots[y] = data
    folder.mkdir(parents=True, exist_ok=True)
    write_json(folder / f'rankings-{y}.json', data)
    rebuild(dist, snapshots, city)
    return f'{city}/{y}'

def import_batch(filename, replace=False, dist=DIST):
    batch = json.loads(Path(filename).read_text(encoding='utf-8'))
    if batch.get('schemaVersion') != 1 or not isinstance(batch.get('datasets'), list) or not batch['datasets']:
        raise ValueError('Nieprawidłowy pakiet datasets.')
    all_snapshots = {city: read_snapshots(city_directory(dist, city), city) for city in registered_cities()}
    incoming = {}
    for raw in batch['datasets']:
        data = validate(raw)
        city, y = city_id(data), str(data['rankingYear'])
        identity = (city, y)
        snapshots = all_snapshots[city]
        if identity in incoming:
            raise ValueError(f'Powtórzony rocznik {y}.')
        if y in snapshots and snapshots[y] != data and not replace:
            raise ValueError(f'Rocznik {y} już istnieje i ma inne dane. Wymagane --replace.')
        incoming[identity] = data
    # Validate the whole batch and every conflict before writing any snapshot.
    (dist / 'data').mkdir(parents=True, exist_ok=True)
    for (city, y), data in incoming.items():
        folder = city_directory(dist, city)
        folder.mkdir(parents=True, exist_ok=True)
        if all_snapshots[city].get(y) != data:
            write_json(folder / f'rankings-{y}.json', data)
    rebuild(dist)
    return ', '.join(f'{city}/{y}' for city, y in sorted(incoming))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dodaj i sprawdź rocznik rankingu.')
    parser.add_argument('command', choices=['import', 'import-batch', 'build', 'validate'])
    parser.add_argument('file', nargs='?')
    parser.add_argument('--replace', action='store_true', help='Zezwól na korektę istniejącego rocznika.')
    args = parser.parse_args()
    try:
        if args.command in ('import', 'import-batch'):
            if not args.file: parser.error('Podaj ścieżkę pliku JSON.')
            print('Zaimportowano:', (import_batch if args.command == 'import-batch' else import_snapshot)(args.file, args.replace))
        elif args.command == 'validate':
            if args.file: validate(json.loads(Path(args.file).read_text(encoding='utf-8')))
            else:
                for city in registered_cities(): read_snapshots(city_directory(DIST, city), city)
            print('Dane poprawne.')
        else:
            rebuild()
            print('Zbudowano katalog roczników.')
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f'Błąd danych: {error}\n')
