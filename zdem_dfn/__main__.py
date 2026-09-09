"""Thin entry: allow ``python -m zdem_dfn`` to run the engine pipeline (CLI)."""
from zdem_dfn.main import main

if __name__ == "__main__":
    raise SystemExit(main())
