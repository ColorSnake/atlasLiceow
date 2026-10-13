# Atlas liceów Krakowa

Atlas z mapą Leaflet i historią miejsc. Interfejs HTML/JavaScript znajduje się w `public/atlas`, a serwer Vinext udostępnia import rankingów i bazę Cloudflare D1.

**Obsługa roczników:** dane od 2017 do 2026, wykresy miejsc, zakładka importu stron WaszaEdukacja/otouczelnie oraz eksport CSV i JSON. Instrukcja i sposób przechowywania: [DANE.md](DANE.md).

## Uruchomienie

Wymagany Node.js >=22.13. W katalogu `licea` zainstaluj zależności i zbuduj aplikację:

```sh
npm ci
npm run build
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0000_lean_stepford_cuckoos.sql
npm start -- --port 8765
```

Migrację uruchom tylko przy pierwszym przygotowaniu lokalnej bazy. Wejdź na http://127.0.0.1:8765/. Lokalna baza jest oddzielona od produkcyjnej. Bez serwera można otworzyć `public/atlas/index.html` do przeglądania danych początkowych i eksportu; import i trwały zapis wymagają serwera. Mapa wymaga połączenia z OpenStreetMap.

## Zakres

- 72 szkoły z zestawienia otouczelnie 2026, w tym szkoły dla dorosłych (domyślnie ukryte).
- 70 dopasowanych pozycji WaszaEdukacja 2026; 44 z Perspektyw 2026.
- 65 lokalizacji; dla 7 liceów dla dorosłych brak potwierdzonego adresu/współrzędnych. Nie są umieszczane w losowych punktach: pozostają na liście.
- Profile klas w 48 kartach, rok oferty podany osobno. Przy braku profili aplikacja informuje o braku danych. Wybrane specjalizacje są dodatkowo potwierdzone w źródłach oficjalnych.
- Wyszukiwanie, filtry profilu i publiczności, przełączanie rankingów, klikane znaczniki, panel wyników matury oraz historia miejsc Perspektyw.

To migawka z **2026-10-04**, nie pełny rejestr wszystkich działających liceów. Dane nie aktualizują się samoczynnie.

## Znaczenie liczb

WaszaEdukacja i otouczelnie podają miejsca w Krakowie. Perspektywy podają **oryginalne miejsca w Polsce** — nie przeliczamy ich na autorski ranking miejski. Oznaczenia ex aequo i oryginalna numeracja pozostają niezmienione po filtrowaniu.

Wyniki przedmiotowe w panelu pochodzą z **matury 2025**, wykorzystanej w rankingu otouczelnie 2026. Nie mieszamy ich z maturą 2026. Punktów różnych wydawców nie należy porównywać bezpośrednio. Kategoria profilu jest wyprowadzona z nazwy opublikowanej klasy i nie jest oceną jakości nauczania.

## Źródła

- [WaszaEdukacja](https://waszaedukacja.pl/ranking/krakow/licea): miejsca, punkty; karty szkół: adresy, współrzędne, profile 2026/2027, status publiczności i strony WWW.
- [otouczelnie](https://www.otouczelnie.pl/ranking/208/Ranking-liceow-w-Krakowie-2026): tabela 72 szkół, miejsca, punkty, wyniki i zdawalność matury 2025; pomocniczo karty adresów i profili (bez potwierdzonego roku, jeśli źródło go nie podaje).
- [Perspektywy](https://licea.perspektywy.pl/rankingi/ranking-glowny-liceow/): 44 szkoły z Krakowa w krajowej tabeli, miejsca, punkty i historia. [Metodologia](https://licea.perspektywy.pl/metodologia/metodologia-ranking-licea-2026/): 25% olimpiady, 30% matura obowiązkowa, 45% dodatkowa; nie uwzględnia matury IB.
- [OpenStreetMap](https://www.openstreetmap.org/copyright): podkład i uzupełniające geokodowanie adresów. Wyniki geokodowania sprawdzono pod kątem zgodności adresu i granic Krakowa. To lokalizacja adresu/budynku, nie gwarancja położenia wejścia.
- Oficjalne strony szkół, Gov.pl i rejestr IB: ręczne, jawne uzupełnienia w `school_overrides.json`, każde z adresem źródła. Poprawiono adres szkoły muzycznej Karłowicza na os. Centrum E 2.

Dodatkowo przeanalizowano [egzamin.pl](https://egzamin.pl/licea/krakow/), który publikuje ranking na podstawie średniej trzech matur podstawowych 2026. Nie włączono tych liczb do porównania edycji opartych na maturze 2025. OKE/CKE to źródła wyników egzaminacyjnych, nie samodzielne rankingi.

## Pliki i odtwarzanie danych

- `public/atlas/data/rankings-2026.json`: niezależna migawka rocznika; przyszłe edycje mają własne pliki `rankings-ROK.json`.
- `public/atlas/data/index.json`: katalog dostępnych roczników.
- `dist/`: gotowa aplikacja; generowany `data.json` zawiera najnowszy rocznik, a `data.js` wszystkie roczniki i umożliwia działanie także po otwarciu pliku HTML.
- `school_overrides.json`: udokumentowane korekty i informacje ze źródeł oficjalnych.
- `scripts/`: pobieranie, ekstrakcja, łączenie i weryfikacja danych. To narzędzia do ręcznej aktualizacji, nie automatyczny scraper uruchamiany u odwiedzającego.
- `research/`: lokalny, ignorowany cache źródeł, współrzędnych i zrzutów testowych; nie jest publikowany.

Skrypty zbierające dane są dostosowane do edycji 2026 i uruchamiane z katalogu nadrzędnego (`ranking_liceow`). Nie są automatycznym importerem kolejnych lat. `build_data.py` zapisuje propozycję zmian w `research/candidate-2026.json`, bez nadpisywania opublikowanych roczników. Do importu nowych zestawów i korekt służy `scripts/datasets.py`, opisany w [DANE.md](DANE.md). Istniejący cache kart jest używany ponownie; pełne odświeżenie wymaga jego świadomego zastąpienia. Wydawcy mogą zmienić HTML, rok rankingu lub adresy szkół. Geokodowanie korzysta z cache i wykonuje zapytania kolejno, z przerwą ponad sekundy.

## Weryfikacja

`scripts/verify.cjs` sprawdza spójność wyników i działanie interfejsu w Playwright/Edge: mapę, wybór szkoły, rankingi, filtry, pusty wynik, licea dla dorosłych, dialog źródeł oraz widok mobilny. Wymaga Node.js 20+, Playwright i uruchomionego lokalnego podglądu. W tym środowisku używa dołączonego runtime; aplikacja sama nie ma tych zależności.

Opcjonalne narzędzie `show_school` jest rejestrowane wyłącznie, gdy przeglądarka udostępnia `document.modelContext`. Natywna obsługa WebMCP nie jest wymagana do działania strony i nie była dostępna do weryfikacji.

## Biblioteka map

Leaflet 1.9.4, licencja BSD-2-Clause w `dist/vendor/LEAFLET-LICENSE`. Leaflet.markercluster 1.5.3, licencja MIT w `dist/vendor/MARKERCLUSTER-LICENSE`. Blisko położone szkoły są grupowane w kafelek z liczbą szkół. Kliknięcie przybliża grupę; przy wspólnym adresie znaczniki rozwijają się, aby można było wybrać każdą szkołę. Zapisane współrzędne pozostają niezmienione.
