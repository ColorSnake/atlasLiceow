# Atlas liceów Krakowa

Interaktywna mapa liceów w Krakowie z rankingami WaszaEdukacja, otouczelnie i Perspektywy, historią wyników 2017–2026 oraz eksportem CSV i JSON. Publiczna aplikacja służy wyłącznie do odczytu. Nowe roczniki dodaje się lokalnym skryptem i publikuje przez Git. Kod aplikacji znajduje się w `licea/`.

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
npm start -- --port 8765
```

Otwórz [lokalną aplikację](http://127.0.0.1:8765/). Baza D1 i logowanie nie są wymagane.

## Układ repozytorium

| Ścieżka | Zawartość |
| --- | --- |
| `licea/public/atlas/` | Interfejs HTML/JavaScript, Leaflet i pliki danych |
| `licea/app/`, `licea/server/` | Aplikacja Vinext, API odczytu i opublikowane dane |
| `licea/db/`, `licea/drizzle/` | Zachowany schemat dawnej bazy D1; aktualna aplikacja go nie używa |
| `licea/scripts/`, `licea/imports/` | Narzędzia danych, testy i pakiet historyczny |
| `docs/` | Dokumentacja techniczna i historia Git |
| `migrate_gui.py`, `package_gui.py` | Historyczne narzędzia migracji i pakowania |

Lokalne katalogi stagingowe, `gui-server-starter/` i archiwa wdrożeniowe są ignorowane. Zależności, wyniki budowania, cache źródeł, pliki środowiskowe i lokalna baza również pozostają poza Git.

## Dostęp i licencje

Publiczna strona nie udostępnia importu ani zapisu: endpointy `/api/import/*` zostały usunięte. Dane pochodzą z wersjonowanych plików, a dawne aktualizacje D1 nie zastępują ich. Eksport pozostaje dostępny dla wszystkich odwiedzających. Instrukcja corocznej aktualizacji jest w [dokumentacji uruchomienia](docs/URUCHOMIENIE.md).

Licencje Leaflet i MarkerCluster znajdują się w `licea/public/atlas/vendor/`, a pozostałe dołączone licencje przy bibliotekach. Repozytorium nie definiuje odrębnej licencji własnego kodu. Lista źródeł danych jest w dokumentacji aplikacji.
