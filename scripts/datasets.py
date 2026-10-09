"""Manage annual snapshots. Python 3.9+, standard library only."""
import argparse
import datetime
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).absolute().parent.parent
DIST = ROOT / 'dist'

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
        require(coords is None or (isinstance(coords, list) and len(coords) == 2 and all(number(c) for c in coords) and 49.9 < coords[0] < 50.2 and 19.7 < coords[1] < 20.3), f'{s["id"]}: współrzędne poza Krakowem lub zły format.')
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

def read_snapshots(directory):
    result = {}
    for file in sorted(directory.glob('rankings-*.json')):
        data = validate(json.loads(file.read_text(encoding='utf-8')))
        y = str(data['rankingYear'])
        if file.name != f'rankings-{y}.json' or y in result:
            raise ValueError(f'Nazwa pliku nie odpowiada rankingYear: {file.name}')
        result[y] = data
    return result

def write_json(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)

def rebuild(dist=DIST, snapshots=None):
    snapshots = snapshots if snapshots is not None else read_snapshots(dist / 'data')
    if not snapshots:
        raise ValueError('Brak roczników.')
    latest = max(snapshots, key=int)
    # Bundle enables direct file:// use, without fetch/CORS or a backend.
    bundle = 'window.SCHOOL_DATASETS = ' + json.dumps(snapshots, ensure_ascii=False, allow_nan=False) + ';\n'
    bundle += f'window.SCHOOL_DATA = window.SCHOOL_DATASETS["{latest}"];\n'
    temporary = dist / 'data.js.tmp'
    temporary.write_text(bundle, encoding='utf-8')
    temporary.replace(dist / 'data.js')
    write_json(dist / 'data.json', snapshots[latest])
    write_json(dist / 'data' / 'index.json', {'schemaVersion': 1, 'defaultYear': int(latest), 'years': sorted(map(int, snapshots), reverse=True)})

def import_snapshot(filename, replace=False, dist=DIST):
    data = validate(json.loads(Path(filename).read_text(encoding='utf-8')))
    folder = dist / 'data'
    snapshots = read_snapshots(folder)
    y = str(data['rankingYear'])
    if y in snapshots and not replace:
        raise ValueError(f'Rocznik {y} już istnieje. Użyj --replace tylko przy świadomej korekcie tego rocznika.')
    snapshots[y] = data
    folder.mkdir(parents=True, exist_ok=True)
    write_json(folder / f'rankings-{y}.json', data)
    rebuild(dist, snapshots)
    return y

def import_batch(filename, replace=False, dist=DIST):
    batch = json.loads(Path(filename).read_text(encoding='utf-8'))
    if batch.get('schemaVersion') != 1 or not isinstance(batch.get('datasets'), list) or not batch['datasets']:
        raise ValueError('Nieprawidłowy pakiet datasets.')
    snapshots = read_snapshots(dist / 'data')
    incoming = {}
    for raw in batch['datasets']:
        data = validate(raw)
        y = str(data['rankingYear'])
        if y in incoming:
            raise ValueError(f'Powtórzony rocznik {y}.')
        if y in snapshots and snapshots[y] != data and not replace:
            raise ValueError(f'Rocznik {y} już istnieje i ma inne dane. Wymagane --replace.')
        incoming[y] = data
    # Validate the whole batch and every conflict before writing any snapshot.
    (dist / 'data').mkdir(parents=True, exist_ok=True)
    for y, data in incoming.items():
        if snapshots.get(y) != data:
            write_json(dist / 'data' / f'rankings-{y}.json', data)
    snapshots.update(incoming)
    rebuild(dist, snapshots)
    return ', '.join(sorted(incoming))

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
            else: read_snapshots(DIST / 'data')
            print('Dane poprawne.')
        else:
            rebuild()
            print('Zbudowano katalog roczników.')
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f'Błąd danych: {error}\n')
