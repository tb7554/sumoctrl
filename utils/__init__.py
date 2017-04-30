# #!/usr/bin/env python
"""
@file   utils/__init__.py
@author  Tim Barker
@date    30/04/2017

"""

import os, sys, pickle, socket

# Functions for handling pickle objects
def save_obj(obj, name ):
    """Save an object to a pickle file"""
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    """Load an object from a pickle file"""
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)

# Functions for running across a cluster
def get_open_port():
    """Checks for an open port which can then be used by TraCI"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

# Functions for navigating directory structures
def add_sumo_tools_to_path():
    """CHecks for SUMO_HOME environment variable and appends tools directory to python path.
    Returns error if no SUMO_HOME variable defined."""
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("Error: Please declare environment variable 'SUMO_HOME'")