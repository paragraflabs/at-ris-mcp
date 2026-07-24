"""stdio entrypoint: ``python -m ris_mcp`` / console script ``at-ris-mcp``."""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 at-ris-mcp contributors

from __future__ import annotations

from .server import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
