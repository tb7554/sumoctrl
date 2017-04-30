# #!/usr/bin/env python
"""
@file   runsim/__init__.py
@author  Tim Barker
@date    05/03/2017

"""

import subprocess, sys
from utils import add_sumo_tools_to_path

import traci

def launch_sumo_process(sumo_config_file, traci_port, sumo_binary="sumo", gui_on=False):
    """Takes a SUMO config file and optional path to the SUMO binary and optional argument to launch SUMO with a gui.
     Launches a SUMO simulation using the subprocess module with a free port open for TraCI. Returns the subprocess and
     traci port number"""

    if gui_on: sumo_binary += "-gui"  # Append the gui command if requested

    sumo_command = ("%s -c %s --remote-port %d" % (sumo_binary, sumo_config_file, traci_port))

    print("Launching process: %s" % sumo_command)
    sumo_subprocess = subprocess.Popen(sumo_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)

    # Open up traci on a free port
    traci.init(traci_port)
    print("Port opened on %d" % traci_port)

    return sumo_subprocess

