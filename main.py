import os
from pathlib import Path

from mistralai import agents

FILES_ROOT = Path(os.environ.get("UGOT_FILES_DIR", ".")).resolve()
MAX_FILE_BYTES = 1_000_000


def _resolve(path: str) -> Path:
    candidate = (FILES_ROOT / path).resolve() if path else FILES_ROOT
    if candidate != FILES_ROOT and FILES_ROOT not in candidate.parents:
        raise agents.ToolError(f"Ścieżka '{path}' wykracza poza dozwolony folder plików.")
    return candidate


@agents.tool(model_access="direct")
async def ugot_list_files(path: str = "") -> list[str]:
    """Wypisz pliki i podfoldery w danym folderze (ścieżka względna wobec folderu plików agenta). Zwraca listę wpisów z typu: 'plik' albo 'folder'."""
    target = _resolve(path)
    if not target.exists():
        raise agents.ToolError(f"Folder '{path or '.'}' nie istnieje.")
    if not target.is_dir():
        raise agents.ToolError(f"'{path}' nie jest folderem.")
    entries = []
    for child in sorted(target.iterdir(), key=lambda p: p.name.lower()):
        kind = "folder" if child.is_dir() else "plik"
        size = "" if child.is_dir() else f" ({child.stat().st_size} B)"
        entries.append(f"{kind}: {child.name}{size}")
    return entries or ["(folder jest pusty)"]


@agents.tool(model_access="direct")
async def ugot_read_file(path: str, start_line: int = 1, max_lines: int = 200) -> str:
    """Przeczytaj plik tekstowy (ścieżka względna), od danej linii, maksymalnie max_lines linii. Zwraca fragment treści z numerami linii."""
    target = _resolve(path)
    if not target.is_file():
        raise agents.ToolError(f"Plik '{path}' nie istnieje.")
    if target.stat().st_size > MAX_FILE_BYTES:
        raise agents.ToolError(
            f"Plik '{path}' jest większy niż {MAX_FILE_BYTES} bajtów; użyj search_files, aby znaleźć konkretne fragmenty."
        )
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise agents.ToolError(f"Nie udało się odczytać pliku '{path}': {exc}") from exc
    lines = text.splitlines()
    if start_line < 1:
        start_line = 1
    window = lines[start_line - 1 : start_line - 1 + max_lines]
    if not window:
        return f"(brak treści: plik ma {len(lines)} linii, żądano od linii {start_line})"
    numbered = "\n".join(f"{i}: {line}" for i, line in enumerate(window, start=start_line))
    total = f"\n\n[linie {start_line}–{start_line + len(window) - 1} z {len(lines)}]"
    return numbered + total


@agents.tool(model_access="direct")
async def ugot_search_files(query: str, path: str = "", max_results: int = 50) -> list[str]:
    """Przeszukaj treść plików tekstowych w danym folderze (rekurencyjnie) w poszukiwaniu tekstu; zwraca trafienia jako 'ścieżka: numer linii: fragment'."""
    target = _resolve(path)
    if not target.exists():
        raise agents.ToolError(f"Folder '{path or '.'}' nie istnieje.")
    needle = query.lower()
    hits: list[str] = []
    for file in sorted(target.rglob("*")):
        if not file.is_file() or file.stat().st_size > MAX_FILE_BYTES:
            continue
        if any(part.startswith(".") for part in file.relative_to(FILES_ROOT).parts):
            continue
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if needle in line.lower():
                hits.append(f"{file.relative_to(FILES_ROOT)}: {number}: {line.strip()[:300]}")
                if len(hits) >= max_results:
                    return hits
    return hits or [f"(brak trafień dla '{query}')"]


agent = agents.Agent(
    model="mistral-large-4",
    name="ugot-assistant",
    instructions=(
        "Jesteś konwersacyjnym asystentem plików pracującym na komputerze użytkownika "
        f"(folder plików: {FILES_ROOT}). Odpowiadasz po polsku, zwięźle i konkretnie. "
        "Gdy użytkownik pyta o swoje pliki, korzystaj z narzędzi ugot_list_files, "
        "ugot_read_file i ugot_search_files, żeby znaleźć i przeczytać właściwą treść, zanim odpowiesz. "
        "Zawsze podawaj ścieżkę pliku i numery linii, na których opierasz odpowiedź. "
        "Pamiętaj kontekst całej rozmowy: jeśli użytkownik pyta dalej o plik albo temat "
        "omawiany wcześniej, nie proś o ponowne wyjaśnienie, tylko użyj tego, co już wiesz. "
        "Jeśli czegoś brakuje, powiedz wprost, czego nie znalazłeś."
    ),
    tools=[ugot_list_files, ugot_read_file, ugot_search_files],
)


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        result = await agent.run("Wypisz, jakie pliki masz w folderze plików.")
        print(result.text)

    asyncio.run(main())
