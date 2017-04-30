# #!/usr/bin/env python
"""
@file   runsim/__init__.py
@author  Tim Barker
@date    05/03/2017

"""

import pickle, socket, os, subprocess, sys
import traci

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

def launch_sumo_process(sumo_config_file, traci_port, sumo_binary="sumo", gui_on=False):
    """Takes a SUMO config file and optional path to the SUMO binary and optional argument to launch SUMO with a gui.
     Launches a SUMO simulation using the subprocess module with a free port open for TraCI. Returns the subprocess and
     traci port number"""

    if gui_on: sumo_binary += "-gui"  # Append the gui command if requested

    sumoCommand = ("%s -c %s --remote-port %d" % \
    (sumo_binary, sumo_config_file, traci_port))

    print("Launched process: %s" % sumoCommand)
    sumo_subprocess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)

    # Open up traci on a free port
    traci.init(traci_port)
    print("Port opened on %d" % traci_port)

    return sumo_subprocess

