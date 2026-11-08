# Uruchomienie i utrzymanie

Publiczna aplikacja pozwala wybierać miasto, przeglądać rankingi i zdawalność matur oraz eksportować dane. Nowe miasta i roczniki dodaje się lokalnym skryptem i publikuje przez GitHub oraz Cloudflare. Nie ma logowania ani operacji zapisu na stronie.

## Wymagania

- Node.js >=22.13.0 oraz npm; sprawdź `node --version` i kolejność PATH.
- Python >=3.9 do importu i walidacji danych; importer używa wyłącznie biblioteki standardowej.
- Internet przy instalacji zależności i pobieraniu kafelków mapy.
- Playwright i Edge do istniejących testów przeglądarkowych, poza zależnościami aplikacji.

Poniższe polecenia wykonuj w `licea/`, chyba że zaznaczono inaczej.

## Uruchomienie lokalne

```powershell
npm ci
npm run build
npm start -- --port 8765
```

Otwórz `http://127.0.0.1:8765/`. Ścieżka `/` przekierowuje na `/atlas/index.html`. Zatrzymanie: Ctrl+C. Kolejne uruchomienia gotowej wersji wymagają tylko `npm start -- --port 8765`; po zmianach wykonaj ponownie build. Baza D1 i migracje nie są wymagane.

Praca nad kodem: `npm run dev -- --hostname 127.0.0.1` albo `uruchom.bat`. Profil portable domyślnie wybiera port 5173; użyj adresu wypisanego przez serwer. Profil lokalny znajduje się w ignorowanym `.sites-runtime/execution-profile.json`. Czysty klon używa profilu portable. Testy przeglądarkowe zakładają port 8765.

Otwarcie `public/atlas/index.html` bez serwera pozwala przeglądać i eksportować dołączone dane. Po nieudanym odczycie API pojawia się informacja o korzystaniu z kopii plikowej. Kafelki mapy wymagają internetu.

## Coroczna aktualizacja danych

1. Przygotuj kompletny JSON nowej edycji zgodny z [DANE.md](../licea/DANE.md). Zachowaj identyfikatory szkół, podaj rzeczywiste źródła oraz lata rankingu i matur. Wpisz `city: "wroclaw"` dla Wrocławia; stare pliki bez `city` należą do Krakowa. Nie kopiuj wyników innego miasta ani starej edycji pod nowy rok.
2. W katalogu `licea/` sprawdź i zaimportuj dane:

```powershell
python scripts/datasets.py validate C:\dane\rankings-2027.json
python scripts/datasets.py import C:\dane\rankings-2027.json
python scripts/test_datasets.py
npm run build
```

Importer automatycznie zapisuje rocznik w katalogu jego miasta i regeneruje katalogi, `data.js`, `data.json` miasta domyślnego oraz `server/seed.json`. Nie trzeba osobno uruchamiać `seed-server.py`. Najnowszy rok miasta staje się domyślny, a poprzednie roczniki i inne miasta pozostają dostępne. Dodanie kolejnego miasta opisuje [plan rozwoju](ROZWOJ.md).

Korekta istniejącej edycji wymaga świadomego zastąpienia:

```powershell
python scripts/datasets.py import C:\dane\poprawione-2026.json --replace
```

Po ręcznej edycji plików `public/atlas/data/rankings-ROK.json` uruchom `python scripts/datasets.py build`, aby odtworzyć wszystkie pliki generowane. Walidacja sprawdza strukturę i zakresy wartości, nie prawdziwość wyników u wydawcy.

3. Uruchom stronę lokalnie i sprawdź nowy rok, szkoły, źródła i eksport.
4. Wróć do katalogu głównego repozytorium i przejrzyj oraz zapisz zmiany:

```powershell
cd ..
git diff --stat
git diff -- licea/public/atlas/data
git add -- licea/public/atlas/data licea/public/atlas/data.js licea/public/atlas/data.json licea/server/seed.json
git diff --cached --stat
git commit -m "data: dodanie rankingu 2027"
git push origin main
```

Polecenia Git wykonuj z katalogu głównego, ponieważ oryginalny katalog roboczy nadal ma dawne `licea/.git`. Nie dodawaj cache `research/`, zależności ani wyników buildu.

5. Poczekaj na udany build i deploy w Cloudflare. Następnie sprawdź nowy rocznik na opublikowanej stronie. Sam lokalny import nie zmienia strony internetowej.

Pakiet historyczny jest już dołączony; ponowny import: `python scripts/datasets.py import-batch imports/historical-batch.json`.

## Cloudflare Workers

| Pole | Wartość |
| --- | --- |
| Root directory | `licea` |
| Build command | `npm ci && npm run build` |
| Deploy command | `npx wrangler deploy --config dist/server/wrangler.json` |
| Node.js | 22.13 lub nowszy |

Dotychczasowa komenda budowania może pozostać. Cloudflare może również sam instalować zależności. Nazwa Workera powinna odpowiadać projektowi `atlasliceow`.

`.openai/hosting.json` ma `d1: null`. Build nie wymaga `CLOUDFLARE_D1_DATABASE_ID` ani `CLOUDFLARE_D1_DATABASE_NAME`; dawne zmienne można usunąć z sekcji Build. Konfiguracja Wranglera jest generowana — nie edytuj `dist/server/wrangler.json` ręcznie.

Aplikacja nie czyta ani nie zapisuje dawnej bazy D1. Istniejąca baza nie jest kasowana. Źródłem danych są wyłącznie pliki w Git; dawne rekordy nie przesłonią nowej edycji. Przed tą zmianą porównano opublikowane dane z repozytorium i nie znaleziono różnic.

## Weryfikacja

```powershell
python scripts/test_datasets.py
node scripts/test-import.mjs
node scripts/verify-gui.cjs
```

- Test Python sprawdza walidację, import i ochronę przed nadpisaniem. Działa w katalogach tymczasowych.
- `test-import.mjs` sprawdza zachowane narzędzia parsowania i scalania. Wymaga ignorowanego cache HTML w `research/`; nie wywołuje już żadnego publicznego importera.
- `verify-gui.cjs` wymaga uruchomionej lokalnej strony. Sprawdza brak importu, eksport CSV/JSON, widok mobilny, zgodność API z seedami i odrzucenie żądań do usuniętych endpointów. Nie zapisuje do bazy ani nie pobiera rankingów od wydawców.
- `verify.cjs` sprawdza mapę, filtry i historię; uruchamiaj z katalogu głównego: `node licea/scripts/verify.cjs`.
- `verify-cities.cjs` sprawdza Wrocław, rozdzielenie roczników, centrum mapy, zdawalność z rokiem matury, brakujące wartości, eksport, widok mobilny i odnośnik `?city=wroclaw`. Uruchamiaj w `licea/`: `node scripts/verify-cities.cjs`.

Skrypty przeglądarkowe zawierają ścieżkę Playwright komputera autora; na innym komputerze dostosuj import. Zrzuty testu mapy trafiają do `licea/research/`. Dawny `verify-conflicts.mjs` został usunięty wraz z importerem serwerowym.

## Narzędzia historyczne i problemy

`migrate_gui.py` i `package_gui.py` to stare narzędzia migracji i pakowania; nie uruchamiaj ich na aktualnym projekcie do zwykłego wdrożenia. Schemat `db/` i migracje `drizzle/` pozostały jako historia dawnej obsługi D1.

| Objaw | Co sprawdzić |
| --- | --- |
| Błąd wersji Node | `node --version` i PATH |
| Brak `dist/server/wrangler.json` | Wykonaj `npm run build` |
| Nowy rok nie pojawia się | Import, pliki generowane i seed w jednym commicie; udany deploy tego commita |
| API pokazuje stare dane | Czy wdrożono najnowszy commit i odtworzono seed przez `datasets.py` |
| Stary formularz importu jest widoczny | Odśwież stronę bez cache po zakończeniu deployu |
| `/api/import/*` zwraca 404 | Prawidłowo: publiczny importer został usunięty |
