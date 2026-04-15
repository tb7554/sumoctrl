# #!/usr/bin/env python
"""
@file   test/conftest.py
@author  Tim Barker (regression harness added by Claude 2026-04-15)
@date    15/04/2026

Pytest configuration for the sumoctrl regression harness.

Ensures the repository root is on sys.path so the absolute imports used
throughout the project (e.g. `from utils import ...`, `from interface
import getdata`) resolve when running `pytest` from any directory.

Also discovers $SUMO_HOME and appends $SUMO_HOME/tools so sumolib and
traci are importable. If SUMO_HOME is not set, tests that need sumolib
will be skipped by the per-test guards.
"""
from __future__ import print_function

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

_sumo_home = os.environ.get("SUMO_HOME")
if _sumo_home:
    _tools = os.path.join(_sumo_home, "tools")
    if _tools not in sys.path:
        sys.path.insert(0, _tools)
