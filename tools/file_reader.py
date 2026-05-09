from pathlib import Path
from langchain_core.tools import tool


@tool
def read_file(path: str) -> str:
    """Read a local file and return its contents. Supports text files (.txt, .md, .py, .csv, .json, etc.) and PDFs."""
    p = Path(path).expanduser().resolve()

    if not p.exists():
        return f"File not found: {path}"
    if not p.is_file():
        return f"Not a file: {path}"

    try:
        if p.suffix.lower() == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(p))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                return text[:15000] or "Could not extract text from this PDF."
            except ImportError:
                return "PDF reading requires pypdf. Run: pip install pypdf"
        else:
            content = p.read_text(encoding="utf-8", errors="ignore")
            return content[:15000]
    except Exception as e:
        return f"Error reading file: {e}"
