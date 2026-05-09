import subprocess
import sys
from langchain_core.tools import tool

CODE_TIMEOUT = 15


@tool
def run_python(code: str) -> str:
    """Execute Python code and return the output. Use for calculations, data processing, analysis, or anything requiring computation."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=CODE_TIMEOUT,
        )
        out = result.stdout.strip()
        err = result.stderr.strip()

        if out and err:
            return f"{out}\n\nSTDERR:\n{err}"
        return out or err or "(no output)"

    except subprocess.TimeoutExpired:
        return f"Timed out after {CODE_TIMEOUT}s."
    except Exception as e:
        return f"Error: {e}"
