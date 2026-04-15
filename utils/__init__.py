# #!/usr/bin/env python
"""
@file   utils/__init__.py
@author  Tim Barker
@date    15/04/2026

"""

import os
import pickle
import socket
import sys
from typing import Any


# Functions for handling pickle objects
def save_obj(obj: Any, name: str) -> None:
    """Save an object to a pickle file (`.pkl` suffix appended to `name`)."""
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name: str) -> Any:
    """Load an object from a pickle file (`.pkl` suffix appended to `name`)."""
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


# Functions for running across a cluster
def get_open_port() -> int:
    """Checks for an open port which can then be used by TraCI."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


# Functions for navigating directory structures
def add_sumo_tools_to_path() -> None:
    """Checks for SUMO_HOME environment variable and appends the tools
    directory to the Python path. Exits the process if SUMO_HOME is unset."""
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("Error: Please declare environment variable 'SUMO_HOME'")
