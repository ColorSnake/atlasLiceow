# Rozwój atlasu

## Zakres bieżącej wersji

Atlas obsługuje Kraków (2017–2026) oraz Wrocław (2026). Każde miasto ma oddzielne szkoły, rankingi, źródła, lata, mapę i eksport. Widoczna na liście i w karcie zdawalność matury pochodzi z opublikowanych danych otouczelnie; jej rok egzaminu jest oddzielony od roku rankingu. Brak wyniku pozostaje brakiem, nie zerem.

## Dodanie następnego miasta

1. Dodaj wpis do `licea/cities.json`: stabilny `id`, nazwę `name`, dopełniacz `genitive` (np. `Warszawy`), zakres miejsc `scope` (np. `w Warszawie`), centrum mapy, przybliżenie i prostokątny zakres współrzędnych `[minLat,minLon,maxLat,maxLon]`.
2. Pobierz i sprawdź rzeczywiste dane dla tego miasta z dotychczasowych wydawców. Potwierdź rok i metodologię; nigdy nie przenoś wyników innego miasta. Zachowaj źródła, daty i sumy SHA-256 stron w audycie. Cache HTML pozostaw w ignorowanym `research/`.
3. Przygotuj migawkę w formacie opisanym w [DANE.md](../licea/DANE.md), z polami `city` oraz `schoolType: "liceum"`. Używaj stabilnych identyfikatorów z prefiksem miasta i jawnie sprawdzonych tożsamości szkół. Sam numer LO nie odróżnia szkół publicznych, prywatnych i dla dorosłych.
4. Z katalogu `licea/` uruchom:

```powershell
python scripts/datasets.py validate C:\dane\rankings-warszawa-2026.json
python scripts/datasets.py import C:\dane\rankings-warszawa-2026.json
python scripts/test_datasets.py
npm run build
```

Importer dobierze katalog według `city`, a nie według nazwy pliku wejściowego. Dla nowych miast używa `public/atlas/data/IDENTYFIKATOR/rankings-ROK.json`. Ten sam rok może występować równolegle w kilku miastach. Domyślnie nie wolno zastępować istniejącej pary miasto–rok; świadoma korekta wymaga `--replace`.

5. Sprawdź mapę i brak błędnych punktów, zgodność liczby szkół, wszystkie dostępne źródła, rok matury, braki danych, widok mobilny i eksport. Commit powinien zawierać konfigurację miasta, migawkę i audyt oraz generowane katalogi, `data.js` i `server/seed.json`. Nowe miasto pojawi się na stronie po udanym wdrożeniu.

Sam wpis w konfiguracji bez danych nie tworzy pustego miasta w selektorze. Publikowane są tylko miasta mające zwalidowane roczniki.

## Kolejne etapy

Pierwszy etap to pięć dużych miast: Warszawa, Kraków, Wrocław, Łódź i Poznań. W tej zmianie dodano wyłącznie Wrocław; pozostałe wymagają osobnego zebrania i sprawdzenia danych. Dalsze miasta korzystają z tej samej struktury. Historię Wrocławia można rozszerzać tylko rzeczywistymi archiwami wydawców.

Szkoły podstawowe są planem długoterminowym. Egzamin ósmoklasisty nie jest maturą i nie ma takiej samej miary zdawalności. Dlatego obecny importer świadomie przyjmuje tylko `schoolType: "liceum"`. Przed dodaniem podstawówek trzeba ustalić odrębny schemat wyników, źródła, metodologię i oznaczenia interfejsu. Nie dodajemy na razie pustego selektora ani danych zastępczych.

Aktualizacje pozostają lokalne, przez skrypt i Git. Publiczna strona nie otrzymuje logowania ani endpointów zapisu.
