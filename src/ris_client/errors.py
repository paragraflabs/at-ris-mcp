"""Structured errors with stable machine-readable codes.

The MCP wrapper surfaces the ``code`` prefix so callers can iterate
(invalid_arg, not_found, unsupported_format, upstream_error).
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 at-ris-mcp contributors

from __future__ import annotations


class RisError(Exception):
    code = "error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def as_text(self) -> str:
        return f"[{self.code}] {self.message}"


class InvalidArgError(RisError):
    code = "invalid_arg"


class NotFoundError(RisError):
    code = "not_found"


class UnsupportedFormatError(RisError):
    code = "unsupported_format"


class UpstreamError(RisError):
    code = "upstream_error"


class NotImplementedYetError(RisError):
    code = "not_implemented"
