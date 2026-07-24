# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 at-ris-mcp contributors
"""Pytest configuration.

The ``fixtures/`` directory holds saved live RIS responses used by the offline
mapping/textparse tests. It ships with the source repository but is deliberately
excluded from the published sdist. When the tests are run from an installed
package (no fixtures present), the fixture-backed tests are skipped rather than
failing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_FIXTURES = Path(__file__).parent.parent / "fixtures"

# Test modules that read files from fixtures/.
_FIXTURE_MODULES = ("test_mapping", "test_textparse")


def pytest_collection_modifyitems(config, items):
    if _FIXTURES.is_dir():
        return
    skip = pytest.mark.skip(
        reason="fixtures/ not available (running outside the source tree)"
    )
    for item in items:
        if item.module.__name__ in _FIXTURE_MODULES:
            item.add_marker(skip)
