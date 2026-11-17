"""Package source for upload, explicitly excluding secrets, databases, and runtimes."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
ROOT_FILES = (
    "README.md", "requirements.txt", "requirements-dev.txt", ".env.example", ".gitignore",
    "wsgi.py", "database-schema.sql", "prompt.md", "agent-prompt.md", "plan.md",
)


def package(destination=None):
    destination = Path(destination) if destination else ROOT / "dist" / "note-demo.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = [ROOT / name for name in ROOT_FILES if (ROOT / name).is_file()]
    for directory in ("app", "scripts", "seed", "docs", "tests"):
        for path in (ROOT / directory).rglob("*"):
            relative = path.relative_to(ROOT)
            if (path.is_file() and not any(part.startswith(".") or part == "__pycache__" for part in relative.parts)
                    and path.suffix not in {".pyc", ".pyo", ".sqlite3", ".sqlite", ".db", ".zip"}):
                files.append(path)
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, path.relative_to(ROOT).as_posix())
    return destination


if __name__ == "__main__":
    print(f"Source archive: {package()}")

