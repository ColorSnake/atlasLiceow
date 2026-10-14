# Uruchomienie i utrzymanie

## Wymagania

- Node.js >=22.13.0 oraz npm, zgodnie z `licea/package.json`. Sprawdź `node --version`; starszy Node widoczny jako pierwszy w PATH wymaga zmiany PATH lub wskazania właściwego runtime.
- Python do narzędzi danych. Podstawowy importer i jego testy używają biblioteki standardowej; lokalnie dostępny jest Python 3.9. Skrypty badawcze mogą wymagać dodatkowych bibliotek i cache.
- Internet przy instalacji zależności, pobieraniu rankingów i kafelków mapy.
- Playwright i Edge do istniejących testów przeglądarkowych; nie są zależnościami aplikacji.

Poniższe polecenia wykonuj w `licea/`, chyba że zaznaczono inaczej.

## Pierwsze uruchomienie

```powershell
npm ci
npm run build
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0000_lean_stepford_cuckoos.sql
npm start -- --port 8765
```

Otwórz `http://127.0.0.1:8765/`. Ścieżka `/` przekierowuje na `/atlas/index.html`. Zatrzymanie: Ctrl+C. Kolejne uruchomienia gotowej wersji wymagają tylko `npm start -- --port 8765`; po zmianach kodu wykonaj ponownie build.

Migracja tworzy tabele i nie powinna być wykonywana ponownie w przygotowanej bazie. `dist/server/wrangler.json` powstaje przy budowaniu. Lokalny stan D1 w `.wrangler/state` jest oddzielony od produkcji.

## Praca nad kodem

```powershell
npm run dev -- --hostname 127.0.0.1
```

Można też uruchomić `uruchom.bat`. Profil portable domyślnie wybiera port 5173; używaj adresu wypisanego przez serwer. Testy przeglądarkowe zakładają port 8765, więc do nich uruchom zbudowaną aplikację jak wyżej. Lokalny profil jest wybierany w `.sites-runtime/execution-profile.json`. Czysty klon bez tego pliku używa profilu portable; managed-linux korzysta z Vite i bash.

Otwarcie `public/atlas/index.html` bez serwera pozwala przeglądać dane początkowe, ale API i trwały import są wtedy niedostępne. Kafelki mapy wymagają internetu.

## Aktualizacja danych w plikach

```powershell
python scripts/datasets.py validate C:\dane\rankings-2027.json
python scripts/datasets.py import C:\dane\rankings-2027.json
python scripts/seed-server.py
npm run build
```

Plik wejściowy musi zawierać rzeczywiste dane wskazanego rocznika. Importer aktualizuje pliki przeglądarkowe. `seed-server.py` odtwarza `server/seed.json` używany przez API — uruchom go po każdej zmianie roczników. Build nie zastępuje tego kroku. Sprawdź diff przed commitem. Korekta istniejącego rocznika wymaga `--replace`.

Import historii: `python scripts/datasets.py import-batch imports/historical-batch.json`, następnie `python scripts/seed-server.py`. Obecny pakiet jest już dołączony. Format, źródła i ograniczenia: [DANE.md](../licea/DANE.md).

Aktualizacje GUI są zapisywane w D1 i mają pierwszeństwo przed plikami. Ponowne wdrożenie nie zastępuje rocznika obecnego w D1. Przed korektą wyeksportuj JSON aktualnego rocznika. To kopia danych rocznika, a nie całej bazy z rewizjami i podglądami. GUI nie obsługuje importu pliku JSON.

## Weryfikacja

```powershell
python scripts/test_datasets.py
node scripts/test-import.mjs
npm run lint
npm run build
```

| Test | Zakres i wymagania |
| --- | --- |
| `test_datasets.py` | Walidacja, import, ochrona przed nadpisaniem; zapis w katalogach tymczasowych |
| `test-import.mjs` | Parsery HTML i scalanie; wymaga ignorowanego cache `research/history/parsed.json`, HTML oraz `research/wasza-current.html` |
| `verify.cjs` | Mapa, filtry i rankingi; Playwright/Edge oraz działający serwer |
| `verify-gui.cjs` | Import, eksport i trwały zapis; wymaga sieci, zmienia lokalną bazę i zapisuje wyniki do `research/` |
| `verify-conflicts.mjs` | Konflikt rewizji; wymaga sieci i zmienia lokalną bazę |

Test parsera nie zadziała w czystym klonie bez przygotowania źródeł. Testy przeglądarkowe zawierają ścieżki runtime komputera autora. Na innym komputerze dostosuj import Playwright i utwórz `research/`, jeśli go brakuje. Testy zapisujące dane uruchamiaj wyłącznie na lokalnej bazie testowej.

## Wdrożenie i narzędzia historyczne

### Własne konto Cloudflare: Workers + D1

Ustawienia Workers Builds dla repozytorium:

| Pole | Wartość |
| --- | --- |
| Root directory | `licea` |
| Build command | `npm run build` |
| Deploy command | `npx wrangler deploy --config dist/server/wrangler.json` |
| Node.js | 22.13 lub nowszy |

Cloudflare automatycznie instaluje zależności, więc ponowne `npm ci` w build command nie jest potrzebne. Nazwa Workera w wygenerowanej konfiguracji musi odpowiadać projektowi w Cloudflare; Workers Builds może dopasować ją podczas wdrożenia.

1. W panelu Cloudflare otwórz **D1 SQL database**, wybierz **Create Database**, nadaj nazwę np. `atlasliceow-db` i skopiuj jej **Database ID**.
2. W projekcie Worker otwórz **Settings > Build > Build variables and secrets**. Dodaj zwykłe zmienne budowania:
   - `CLOUDFLARE_D1_DATABASE_ID`: rzeczywisty Database ID, w formacie UUID.
   - `CLOUDFLARE_D1_DATABASE_NAME`: nazwa bazy, np. `atlasliceow-db`.
3. Utwórz tabele w nowej bazie. W jej zakładce **Console** wykonaj kolejno poniższe dwa zapytania. Są zgodne ze schematem w `drizzle/0000_lean_stepford_cuckoos.sql`; `IF NOT EXISTS` pozwala bezpiecznie ponowić utworzenie tabel, lecz nie naprawia odmiennego istniejącego schematu.

```sql
CREATE TABLE IF NOT EXISTS annual_snapshots (
  year INTEGER PRIMARY KEY NOT NULL,
  payload TEXT NOT NULL,
  revision INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS import_drafts (
  id TEXT PRIMARY KEY NOT NULL,
  payload TEXT NOT NULL,
  created INTEGER NOT NULL
);
```

4. Wgraj zmieniony `vite.config.ts` do GitHub i ponów build. Konfiguracja w `dist/server/wrangler.json` zostanie wygenerowana z Twoim ID. Binding aplikacji nadal nazywa się `DB`.

Zmienne muszą być dostępne **podczas budowania**, ponieważ Vite zapisuje je w konfiguracji wdrożenia. Sama zmienna runtime lub binding ustawiony tylko w panelu nie zastępuje ID używanego przez Wrangler. Nie edytuj ręcznie `dist/server/wrangler.json`: następny build go odtworzy. Lokalnie bez tych zmiennych pozostaje dotychczasowa baza lokalna. Workers Builds bez ID zatrzyma się z konkretną instrukcją, zanim rozpocznie upload.

Alternatywnie pierwszą migrację nowej bazy można wykonać z terminala po zalogowaniu Wrangler i zbudowaniu aplikacji z rzeczywistym ID:

```powershell
npx wrangler d1 execute DB --remote --config dist/server/wrangler.json --file drizzle/0000_lean_stepford_cuckoos.sql
```

To polecenie dotyczy bazy w Cloudflare i wykonuje pierwotną migrację tylko raz. Dane początkowe roczników są dołączone w `server/seed.json`, więc puste tabele wystarczą do odczytu początkowych rankingów. Przed publicznym uruchomieniem operacji importu zapewnij uprawnienia administratora; kontrola Origin sama nie ogranicza zapisu do właściciela.

Dokumentacja dostawcy: [tworzenie i podłączanie D1](https://developers.cloudflare.com/d1/get-started/), [ustawienia Workers Builds](https://developers.cloudflare.com/workers/ci-cd/builds/configuration/).

Build tworzy Worker i zasoby w `dist/`. Integracja Sites korzysta z `.openai/hosting.json`, kodu `build/` i migracji `drizzle/`. Dokumentacja opisuje kod, nie potwierdza aktualnych ustawień hostingu.

`migrate_gui.py` to jednorazowa migracja starej aplikacji statycznej. Nie uruchamiaj jej na aktualnym projekcie: kopiuje starter i stare `dist` do źródeł. `package_gui.py` ma lokalną ścieżkę helpera Sites i może wykorzystać wcześniejszy staging. Nie jest przenośnym skryptem publikacji. Nowe wdrożenie przygotuj ze świeżego buildu przez integrację hostingu.

## Typowe problemy

| Objaw | Co sprawdzić |
| --- | --- |
| Błąd wersji Node lub składni | `node --version` i kolejność PATH |
| Brak `dist/server/wrangler.json` | Wykonaj `npm run build` |
| API 503 lub ostrzeżenie o kopii początkowej | Binding DB, migrację i lokalny stan D1 |
| Import 400 | Komunikat odpowiedzi, rok, dostępność wydawcy, Origin i Content-Type |
| Import 409 | Pobierz nowy podgląd; rocznik zmienił się od jego przygotowania |
| Podgląd wygasł | Pobierz ponownie; ważność wynosi godzinę |
| Zmiany JSON niewidoczne przez API | Odtwórz seed i build; sprawdź pierwszeństwo danych D1 |
| Błąd Git fsmonitor | Użyj `git -c core.fsmonitor=false status` |
