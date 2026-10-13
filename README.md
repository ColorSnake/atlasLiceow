# Atlas liceów Krakowa

Interaktywna mapa liceów w Krakowie z rankingami WaszaEdukacja, otouczelnie i Perspektywy, historią wyników 2017–2026 oraz importem i eksportem danych. Kod aplikacji znajduje się w `licea/`.

Migawka 2026 obejmuje 72 szkoły, w tym szkoły dla dorosłych. Miejsca WaszaEdukacja i otouczelnie dotyczą Krakowa, a Perspektyw — Polski. Wyniki matur przypisane do edycji otouczelnie 2026 pochodzą z 2025 roku. Dane nie aktualizują się automatycznie.

## Dokumentacja

- [Uruchomienie i utrzymanie](docs/URUCHOMIENIE.md): instalacja, baza, aktualizacja danych, testy i rozwiązywanie problemów.
- [Architektura i API](docs/ARCHITEKTURA.md): przepływ danych, endpointy i trwały zapis.
- [Historia projektu i Git](docs/HISTORIA_GIT.md): zachowane commity i praca z repozytorium.
- [Opis aplikacji i źródła](licea/README.md).
- [Format danych i instrukcja importu](licea/DANE.md).

## Szybki start

Wymagany Node.js **22.13 lub nowszy** z npm. Z katalogu głównego repozytorium:

```powershell
cd licea
node --version
npm ci
npm run build
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0000_lean_stepford_cuckoos.sql
npm start -- --port 8765
```

Migrację SQL wykonaj tylko przy pierwszym przygotowaniu lokalnej bazy. Otwórz [lokalną aplikację](http://127.0.0.1:8765/).

## Układ repozytorium

| Ścieżka | Zawartość |
| --- | --- |
| `licea/public/atlas/` | Interfejs HTML/JavaScript, Leaflet i pliki danych |
| `licea/app/`, `licea/server/` | Aplikacja Vinext, API i logika importu |
| `licea/db/`, `licea/drizzle/` | Schemat i migracja Cloudflare D1 |
| `licea/scripts/`, `licea/imports/` | Narzędzia danych, testy i pakiet historyczny |
| `docs/` | Dokumentacja techniczna i historia Git |
| `migrate_gui.py`, `package_gui.py` | Historyczne narzędzia migracji i pakowania |

Lokalne katalogi stagingowe, `gui-server-starter/` i archiwa wdrożeniowe są ignorowane. Zależności, wyniki budowania, cache źródeł, pliki środowiskowe i lokalna baza również pozostają poza Git.

## Dostęp i licencje

API importu zakłada kontrolę dostępu zapewnianą przez wdrożenie Sites. Sprawdzenie Origin nie jest autoryzacją administratora; przed publicznym udostępnieniem zapisu trzeba dodać uprawnienia. Lokalnie uruchamiaj serwer na adresie pętli zwrotnej.

Licencje Leaflet i MarkerCluster znajdują się w `licea/public/atlas/vendor/`, a pozostałe dołączone licencje przy bibliotekach. Repozytorium nie definiuje odrębnej licencji własnego kodu. Lista źródeł danych jest w dokumentacji aplikacji.
