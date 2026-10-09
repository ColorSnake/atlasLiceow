# Roczniki i dodawanie danych

## Co jest przechowywane

Każdy rok ma niezależną migawkę szkół w `dist/data/rankings-ROK.json`. Stabilne `id` szkoły powinno być takie samo w kolejnych latach. Dla importowanych archiwów historyczne są wyniki rankingowe i matury. Adresy i współrzędne pochodzą z bazy 2026 (pole `metadataAsOf`), a nie ze zweryfikowanych historycznych lokalizacji. Historyczne profile klas pozostają puste. Aplikacja oznacza to przy wyborze roku i w karcie szkoły.

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

Pozostałe pola i pełny przykład rzeczywistego formatu znajdują się w `dist/data/rankings-2026.json`. Format ma `schemaVersion: 1`.

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

- `dist/data/index.json`: dostępne lata i rok domyślny.
- `dist/data.js`: pakiet wszystkich roczników dla przeglądarki; dzięki niemu aplikacja działa też po otwarciu HTML bez serwera.
- `dist/data.json`: kopia najnowszego rocznika, zachowana dla zgodności i wygodnej analizy.

Nie edytuj tych trzech plików ręcznie. Po ręcznej korekcie plików rocznych można uruchomić `python scripts/datasets.py build`. Zalecany jest jednak import, który domyślnie chroni istniejące roczniki.

Nie ma bazy danych, formularza importu w przeglądarce ani automatycznego pobierania nowych lat. Skrypty zbierające dane utworzone w pierwszej wersji są właściwe dla **edycji 2026**. `build_data.py` zapisuje teraz propozycję w `research/candidate-2026.json`; nie nadpisuje aktywnego katalogu. Dla nowych lat należy dopasować pobieranie i parsowanie do stron wydawców, następnie użyć wspólnego importera.

## Testy

`python scripts/test_datasets.py` testuje migrację, walidację, ochronę przed nadpisaniem i zachowanie starszego pliku podczas importu. Testy używają sztucznego przyszłego rocznika wyłącznie w katalogu tymczasowym; nie trafia on do aplikacji. Test przeglądarkowy `verify.cjs` sprawdza również przełączanie roczników na wstrzykniętych danych testowych, bez publikowania fikcyjnych wyników.
