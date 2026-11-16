# ugot-assistant — konwersacyjny agent do Twoich plików

Agent zbudowany na **Mistral Agent SDK** (`mistralai-agents`). Działa jako
self-hosted worker (`agents serve`) **na Twoim komputerze**, ma dostęp do
wskazanego folderu z plikami (np. plików programu UGOT) i odpowiada na pytania
o nie po polsku, w jednej trwałej rozmowie (sesji) — pamięta plik i cały
dotychczasowy kontekst rozmowy.

## Struktura

- `main.py` — definicja agenta `ugot-assistant` i trzy narzędzia plikowe:
  - `ugot_list_files` — listuje pliki i podfoldery,
  - `ugot_read_file` — czyta plik tekstowy (z numerami linii),
  - `ugot_search_files` — przeszukuje treść plików rekurencyjnie.
  Wszystkie działają tylko wewnątrz folderu z `UGOT_FILES_DIR` (ścieżki
  spoza niego są odrzucane) i są tylko do odczytu.
- `test_agent.py` — test narzędzi i test z `ScriptedModel` (bez klucza API).

## Wymagania

- Python 3.12+ i [uv](https://docs.astral.sh/uv/)
- `MISTRAL_API_KEY` z konta Mistral (użytkownik z rolą z dostępem do
  Workflows, np. Developer lub Workspace Contributor)

## Uruchomienie

```bash
cd ugot-files-agent
export MISTRAL_API_KEY="<twój-klucz>"
export UGOT_FILES_DIR="/sciezka/do/folderu/z/plikami"   # np. folder projektu UGOT
uv sync
uv run agents serve
```

Worker zarejestruje agenta `ugot-assistant` i wypisze m.in. link do
**Vibe Code Web**:

```
https://chat.mistral.ai/managed-agents/ugot-assistant?source=agents_api
```

Otwórz go w przeglądarce i rozmawiaj z agentem jak w czacie — sesja jest
trwała, więc agent pamięta całą rozmowę i wczytane pliki między
kolejnymi pytaniami (domyślnie 4 h bezczynności / 24 h życia sesji).

Alternatywnie, z drugiego terminala:

```bash
uv run agents chat ugot-assistant
```

## Uwagi

- Narzędzia agenta wykonują się na komputerze, na którym działa
  `agents serve` — to celowe (dostęp do Twoich plików lokalnych).
- Bez `UGOT_FILES_DIR` agent używa bieżącego folderu roboczego.
- Zatrzymanie `agents serve` (Ctrl+C) kończy odpowiadanie; sesje są
  zapisane i wznawiane po ponownym uruchomieniu.
