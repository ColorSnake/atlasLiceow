# Roczniki i dodawanie danych

## Co jest przechowywane

Każda para miasto–rok ma niezależną migawkę. Kraków zachowuje ścieżkę `public/atlas/data/rankings-ROK.json`, a Wrocław używa `public/atlas/data/wroclaw/rankings-ROK.json`. Stabilne `id` szkoły powinno być takie samo w kolejnych latach jej miasta; identyfikatory Wrocławia mają prefiks `wroclaw-`. Dane i historia nigdy nie łączą się między miastami.

Plik nowego miasta zawiera `city` (np. `wroclaw`) i `schoolType: "liceum"`. Brak tych pól w oryginalnych plikach oznacza Kraków i liceum — nie trzeba przepisywać starych migawek. Miasto musi być zarejestrowane w `cities.json`. Walidacja współrzędnych korzysta z prostokątnego zakresu przypisanego do tego miasta, nie z jednego zakresu Krakowa. To filtr błędów geograficznych, nie dowód poprawności adresu.

Dla archiwów Krakowa historyczne są wyniki rankingowe i matury. Adresy i współrzędne pochodzą z bazy 2026 (`metadataAsOf`), a nie ze zweryfikowanych historycznych lokalizacji. Historyczne profile pozostają puste. Wrocław rozpoczyna się od 2026; brakujących edycji nie uzupełniamy fikcyjnymi wynikami.

## Pakiet historyczny 2017–2025

`imports/historical-batch.json` zawiera dziewięć roczników i 667 pozycji: WaszaEdukacja 2017–2025 oraz otouczelnie 2022–2025. `imports/history-audit.json` zawiera adresy archiwów, datę pobrania, liczbę pozycji oraz SHA-256 pobranych stron. Kopie HTML pozostają lokalnie w `research/history` (nie są publikowane).

Uruchom `importuj_historie.bat` lub `python scripts/datasets.py import-batch imports/historical-batch.json`. Pakiet jest już zaimportowany do aplikacji. Ponowny identyczny import jest bezpieczny. Walidacja całego pakietu i konflikty są sprawdzane przed zapisem; zmiana istniejących danych wymaga `--replace`. Operacje zapisu nie są transakcją bazy danych; po awarii dysku należy ponowić import.

Wykres przedstawia jeden wybrany ranking, aby nie mieszać miejsc miejskich i ogólnopolskich. Braki przerywają linię; tabela zawiera dokładne miejsca i źródła. Dla Perspektyw starsze miejsca 2023–2025 pochodzą z tabeli historii edycji 2026, co jest opisane przy linku. Metodologia i liczba szkół mogą zmieniać się między latami.

Odtworzenie pakietu: `python scripts/fetch_history.py`, `python scripts/parse_history.py`, `python scripts/build_history.py`. Pobieranie korzysta z lokalnej pamięci podręcznej. Skrypt tożsamości korzysta z jawnych reguł nazw oraz adresów kart wydawców; nowe nierozpoznane szkoły wymagają przeglądu. Nie dopasowuje nazw rozmycie.

W pliku rozróżniamy:

- `rankingYear`: rok edycji rankingu, np. 2026.
- `examYear`: rok wyników matury z otouczelnie, np. 2025. Może być `null`, jeśli rok jest niepotwierdzony lub różny w szkołach. Każda szkoła ma też własne `examYear`; przy niepustym roku zestawu wartości muszą być zgodne.
- `schools[].profileYear`: rok szkolny oferty, np. `2026/2027`, lub `Rok oferty niepotwierdzony`.
- `updated`: data faktycznego zebrania/weryfikacji danych (YYYY-MM-DD), a nie data publikacji kodu.
- `sources`: nazwy, adresy źródeł, objaśnienia metodologii, zakres numeracji i precyzja punktów **dla tej edycji**. Zmiana samego numeru roku nie aktualizuje danych ani metodologii.

Pozostałe pola i pełny przykład rzeczywistego formatu znajdują się w `public/atlas/data/rankings-2026.json`. Format ma `schemaVersion: 1`.

`schools` to lista kart z polami: `id`, `name`, `address`, `type`, `adult`, `coords` (para szerokość/długość geograficzna albo `null`), `examYear`, `profiles`, `profileYear`, `profileSource`, `tags`, `rankings`. Opcjonalne są m.in. `website`, `coordSource`, `addressSource`, `specialization`, `specializationSource`.

`rankings` używa kluczy `wasza`, `pers`, `oto`. Wartość `null` lub brak klucza oznacza brak danych; nigdy nie wpisuj zera jako brakującego miejsca. Rekord rankingu zawiera `rank` (np. `58=`), `score`, opcjonalnie `url`, a dla otouczelnie także procenty `polish`, `math`, `english`, `passRate` (brakujący procent to `null`). Historia Perspektyw ma postać `history: {"2025": "2"}`. Roczniki historii muszą poprzedzać rok rankingu. To nadal format obecnych trzech wydawców; nowy wydawca lub inny model egzaminu wymagają dostosowania aplikacji.

## Import nowego rocznika

1. Przygotuj JSON z **rzeczywistymi danymi nowej edycji**, zachowując powyższy format. Uzupełnij źródła i lata. Nie kopiuj wyników 2026 pod nazwą 2027.
2. W katalogu `licea` uruchom:

```powershell
python scripts/datasets.py validate "C:\dane\rankings-2027.json"
python scripts/datasets.py import "C:\dane\rankings-2027.json"
```

Importer sprawdzi cały zestaw, zapisze osobny plik, doda go do katalogu roczników i wygeneruje pliki przeglądarkowe. Najnowszy dostępny rok staje się domyślny. Starsze pliki pozostają bez zmian. Po odświeżeniu lokalnej aplikacji nowy rok pojawi się w selektorze. Wersja internetowa wymaga ponownej publikacji.

Korekta istniejącej edycji wymaga jawnego `--replace`:

```powershell
python scripts/datasets.py import "C:\dane\poprawione-2026.json" --replace
```

Zachowaj kopię i przejrzyj zmiany przed zastąpieniem istniejącej edycji. Walidacja sprawdza strukturę i zakresy wartości, **nie potwierdza prawdziwości danych u wydawcy**. Równoległe uruchamianie kilku importów nie jest obsługiwane.

## Pliki generowane

- `public/atlas/data/index.json`: katalog dostępnych miast i lata miasta domyślnego; osobne katalogi miast mają własny `index.json`.
- `public/atlas/data.js`: `window.SCHOOL_CATALOG` z miastami i rocznikami, a także zgodne ze starszą wersją aliasy domyślnego miasta; dzięki temu aplikacja działa też po otwarciu HTML bez serwera.
- `public/atlas/data.json`: kopia najnowszego rocznika, zachowana dla zgodności i wygodnej analizy.
- `server/seed.json`: ten sam katalog miast i roczników dla API odczytu; importer aktualizuje go automatycznie.

Nie edytuj tych plików ręcznie. Po ręcznej korekcie plików rocznych można uruchomić `python scripts/datasets.py build`. Zalecany jest jednak import, który domyślnie chroni istniejące roczniki. Dodaj plik rocznika i wszystkie pliki generowane do jednego commita. Nowa wersja danych pojawi się publicznie dopiero po wdrożeniu tego commita przez Cloudflare.

## Publiczna strona: tylko odczyt i eksport

Zakładka **Dane · eksport** pozwala pobrać opublikowany rocznik jako CSV albo JSON. Na stronie nie ma logowania, formularza importu, podglądu zmian ani przycisku zapisu.

Endpointy `/api/import/preview`, `/api/import/prepare` i `/api/import/commit` zostały usunięte. Wywołanie ich bezpośrednio również nie aktualizuje danych. `GET /api/datasets` zwraca `{catalog, revisions: {}}`. `catalog` zawiera `defaultCity`, metadane `cities` oraz `datasetsByCity[miasto][rok]`, wyłącznie z plików opublikowanych w Git.

Nowe roczniki i poprawki wprowadza się lokalnie przez `scripts/datasets.py`, przegląda w Git i wysyła do repozytorium. Szczegółowa lista poleceń: [coroczna aktualizacja](../docs/URUCHOMIENIE.md#coroczna-aktualizacja-danych).

Pliki wersjonowane w Git są jedynym źródłem opublikowanych danych. Aplikacja nie odczytuje ani nie zapisuje D1, a dawne rekordy bazy nie przesłaniają nowych plików. Istniejąca baza i jej zawartość nie są kasowane. Przed przejściem na ten model sprawdzono, że publiczne roczniki odpowiadają plikom repozytorium; lokalna kopia odpowiedzi pozostała w ignorowanym katalogu `research/`.

Eksport CSV obejmuje wszystkie szkoły i źródła wybranego miasta oraz roku, niezależnie od filtrów mapy: jeden wiersz na parę szkoła–wydawca. Zawiera miasto, typ szkoły, rok matury i zdawalność. Format: UTF-8 z BOM, średnik, CRLF, cudzysłowy; wartości mogące zostać potraktowane jako formuła są poprzedzane apostrofem. JSON zachowuje pełny zestaw wybranego miasta i roku. Nazwa pobranego pliku zawiera identyfikator miasta.

Projekt korzysta z szablonu Vinext i integracji Sites. `npm run dev` uruchamia podgląd, `npm run build` tworzy wynik w `dist`, `npm start` uruchamia zbudowany Worker lokalnie. D1 i migracja SQL nie są potrzebne. Wymagany Node >=22.13. Kopie HTML w `research/history` służą do lokalnych narzędzi i nie trafiają do publikacji.


## Testy

`python scripts/test_datasets.py` testuje migrację, walidację, ochronę przed nadpisaniem i zachowanie starszego pliku podczas importu. Testy używają sztucznego przyszłego rocznika wyłącznie w katalogu tymczasowym; nie trafia on do aplikacji. Test przeglądarkowy `verify.cjs` sprawdza również przełączanie roczników na wstrzykniętych danych testowych, bez publikowania fikcyjnych wyników.
