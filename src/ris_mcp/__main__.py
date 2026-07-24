"""stdio entrypoint: ``python -m ris_mcp`` / console script ``at-ris-mcp``."""

from __future__ import annotations

from .server import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
