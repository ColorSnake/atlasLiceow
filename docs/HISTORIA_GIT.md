# Historia projektu i praca z Git

## Zachowana historia

Katalog główny miał commit `76f1255` (`first commit`) z README. W `licea/.git` istniała osobna historia aplikacji. Opisy poniżej wynikają z zawartości zmian; oryginalne komunikaty brzmiały `Update Site source`.

| Commit | Zawartość |
| --- | --- |
| `3826062` | Pierwszy atlas statyczny: mapa, dane 2026, biblioteki i skrypty pozyskiwania danych |
| `4cf8dd1` | Migawki roczników, katalog danych, walidacja, import JSON i testy |
| `8a37516` | Historia 2017–2025, pakiet i audyt źródeł, import pakietowy i wykres historii |
| `17dc43b` | Vinext, D1, import GUI, eksport i przeniesienie atlasu do `public/atlas` |
| `660b056` | Dołączenie oryginalnej historii i kodu pod `licea/` do repozytorium głównego |

Commit scalający ma obie historie jako przodków. Oryginalne identyfikatory, autorzy i daty są zachowane. Dawne commity używają ścieżek względem dawnego korzenia, np. `dist/app.js`; obecne pliki znajdują się pod `licea/`. Nie tworzono fikcyjnych dat ani etapów rozwoju.

## Przeglądanie

Polecenia uruchamiaj w katalogu głównym `ranking_liceow`:

```powershell
git log --graph --oneline --all
git show --stat 17dc43b
git show 8a37516:DANE.md
git log --first-parent --oneline
git status
```

`--first-parent` pokazuje linię integracji; pełny graf także oryginalną historię. Filtr `git log -- licea/` nie pokaże wszystkich zmian sprzed przeniesienia pod ten prefiks.

## Kolejne zmiany

```powershell
git switch -c codex/opis-zmiany
git diff
git add docs/URUCHOMIENIE.md
git diff --cached
git commit -m "docs: aktualizacja instrukcji uruchomienia"
```

Dodawaj konkretne pliki. Nie wersjonuj zależności, lokalnej bazy, cache, sekretów ani archiwów wdrożeniowych. Seedy i przeglądarkowe pliki danych są wersjonowane, aby czysty klon miał dane początkowe. Po aktualizacji roczników dodaj odpowiadające im pliki generowane.

W oryginalnym katalogu pozostało wewnętrzne `licea/.git`, zachowane bez usuwania. Nie jest częścią głównego repozytorium ani submodułem. Polecenia Git wykonuj z korzenia (lub `git -C D:\projekty\ranking_liceow ...`), aby nie zapisywać nowych commitów wyłącznie w starym repozytorium. Czysty klon ma tylko główny `.git`.

Lokalny commit nie oznacza publikacji strony ani wysłania kodu do zdalnego repozytorium. `origin` było skonfigurowane przed pracami; zdalnej historii nie nadpisywano.
