# #!/usr/bin/env python
"""
@file   runsim/__init__.py
@author  Tim Barker
@date    15/04/2026

"""

import subprocess
import sys

from utils import add_sumo_tools_to_path

add_sumo_tools_to_path()

import traci


def launch_sumo_process(
    sumo_config_file: str,
    traci_port: int,
    sumo_binary: str = "sumo",
    gui_on: bool = False,
) -> subprocess.Popen:
    """Takes a SUMO config file and optional path to the SUMO binary and
    optional argument to launch SUMO with a gui. Launches a SUMO simulation
    using the subprocess module with a free port open for TraCI. Returns
    the subprocess; the caller should ``.wait()`` on it when the
    simulation is over."""

    if gui_on:
        sumo_binary += "-gui"  # Append the gui command if requested

    sumo_command = f"{sumo_binary} -c {sumo_config_file} --remote-port {traci_port}"

    print(f"Launching process: {sumo_command}")
    sumo_subprocess = subprocess.Popen(sumo_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)

    # Open up traci on a free port
    traci.init(traci_port)
    print(f"Port opened on {traci_port}")

    return sumo_subprocess
