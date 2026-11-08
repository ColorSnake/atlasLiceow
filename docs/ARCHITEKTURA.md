# Architektura i API

Publiczna aplikacja jest przeznaczona wyłącznie do odczytu i eksportu. Nie ma logowania, importu przez przeglądarkę ani operacji zapisu na serwerze.

## Przepływ danych

```mermaid
flowchart TD
  JSON[Sprawdzony JSON nowej edycji] --> Import[Lokalny scripts/datasets.py]
  Import --> Files[Pliki roczników w Git]
  Import --> Bundle[data.js i data.json]
  Import --> Seed[server/seed.json]
  Files --> Commit[Commit i push do GitHub]
  Bundle --> Commit
  Seed --> Commit
  Commit --> Deploy[Build i deploy Cloudflare]
  Deploy --> API[GET /api/datasets]
  Deploy --> Static[Pliki atlasu]
  API --> UI[Mapa, filtry i historia]
  Static --> UI
  UI --> Export[Eksport CSV i JSON]
```

Interfejs HTML/CSS/JavaScript znajduje się w `licea/public/atlas/`. Leaflet wyświetla mapę, a MarkerCluster grupuje szkoły. `app.js` obsługuje filtry, karty i historię; `data-manager.js` udostępnia eksport. React/Vinext zapewnia trasę odczytu i przekierowanie `/` na atlas.

`bootstrap.js` odczytuje API z limitem 12 sekund. W razie błędu pozostawia dane z dołączonego `data.js` i pokazuje komunikat. Obie kopie są generowane z tych samych roczników przez lokalny importer. D1 nie bierze udziału w odczycie.

## Pliki danych

| Ścieżka w `licea/` | Rola |
| --- | --- |
| `public/atlas/data/rankings-ROK.json` | Wersjonowane migawki roczników, schemaVersion 1 |
| `public/atlas/data/index.json` | Katalog dostępnych lat i rok domyślny |
| `public/atlas/data.js`, `data.json` | Pakiet przeglądarkowy i najnowsza migawka |
| `server/seed.json` | Te same roczniki dla API odczytu |
| `scripts/datasets.py` | Walidacja, import i generowanie wszystkich kopii, w tym seedów |

Stabilne `schools[].id` łączy szkołę między latami. Brak wyniku nie jest zerem. Dane historyczne nie potwierdzają dawnych adresów ani ofert: lokalizacje korzystają z bazy 2026, a historyczne profile pozostają puste. Schemat i źródła opisuje [DANE.md](../licea/DANE.md).

## API i dostęp

`GET /api/datasets` zwraca `{datasets, revisions: {}}` z nagłówkiem `Cache-Control: no-store`. `revisions` pozostało puste dla zgodności z formatem wcześniejszych odpowiedzi; aplikacja nie prowadzi już rewizji bazy.

Endpointy `/api/import/preview`, `/api/import/prepare` i `/api/import/commit` zostały usunięte, wraz z kodem zapisu D1. Bezpośrednie żądanie do dawnego API również nie zmienia danych. Publiczna mapa i eksport nie wymagają konta. Uprawnienia do zmian wynikają z dostępu do repozytorium GitHub oraz wdrożeń Cloudflare.

`.openai/hosting.json` deklaruje `d1: null`, więc nowy build nie wiąże bazy. Stare rekordy nie zastępują danych z Git. Istniejąca baza i dawne migracje pozostają zachowane; zmiana nie wykonuje żadnego kasowania danych.

## Coroczna publikacja

Właściciel przygotowuje rzeczywisty rocznik, waliduje i importuje go lokalnie, przegląda diff, testuje i wysyła commit z rocznikiem oraz plikami generowanymi. Cloudflare buduje i publikuje nową wersję. Szczegółowe polecenia: [instrukcja aktualizacji](URUCHOMIENIE.md#coroczna-aktualizacja-danych).
