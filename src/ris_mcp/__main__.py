"""Entrypoint for the at-ris-mcp server.

Defaults to **stdio** (``python -m ris_mcp`` / ``at-ris-mcp``). An HTTP/SSE
transport can be selected for remote/hosted deployments, via CLI flags or
environment variables::

    at-ris-mcp                          # stdio (default)
    at-ris-mcp --transport http         # streamable HTTP on 127.0.0.1:8000
    at-ris-mcp --transport sse --port 9000
    RIS_MCP_TRANSPORT=http at-ris-mcp   # same via env

Env vars: ``RIS_MCP_TRANSPORT`` (stdio|http|sse|streamable-http),
``RIS_MCP_HOST``, ``RIS_MCP_PORT``, ``RIS_MCP_PATH``.
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 at-ris-mcp contributors

from __future__ import annotations

import argparse
import os

from .server import mcp

_TRANSPORTS = ("stdio", "http", "sse", "streamable-http")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="at-ris-mcp",
        description="MCP server for the Austrian legal information system (RIS).",
    )
    p.add_argument(
        "--transport",
        choices=_TRANSPORTS,
        default=os.environ.get("RIS_MCP_TRANSPORT", "stdio"),
        help="Transport protocol (default: stdio).",
    )
    p.add_argument(
        "--host",
        default=os.environ.get("RIS_MCP_HOST", "127.0.0.1"),
        help="Bind host for http/sse transports (default: 127.0.0.1).",
    )
    p.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("RIS_MCP_PORT", "8000")),
        help="Bind port for http/sse transports (default: 8000).",
    )
    p.add_argument(
        "--path",
        default=os.environ.get("RIS_MCP_PATH"),
        help="URL path for the HTTP endpoint (transport default if unset).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.transport == "stdio":
        mcp.run()
        return
    # http / sse / streamable-http
    kwargs: dict[str, object] = {
        "transport": args.transport,
        "host": args.host,
        "port": args.port,
    }
    if args.path:
        kwargs["path"] = args.path
    mcp.run(**kwargs)


if __name__ == "__main__":
    main()
