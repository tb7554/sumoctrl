# #!/usr/bin/env python
"""
@file   test/test_interface.py
@author  Tim Barker
@date    30/04/2017

Module for running tests on the functions contained in this package.

"""

import os, sys
from interface import getdata
from runsim import launch_sumo_process, get_open_port

import traci

if __name__ == "__main__":

    traci_port = get_open_port()

    sumo_config_file = 'test_scenario/test.sumocfg'

    sumo_subprocess = launch_sumo_process(sumo_config_file, traci_port, sumo_binary="sumo", gui_on=False)

    lane_sub = getdata.LaneSubscription()

    # initialise the step
    step = 0

    # run the simulation
    while step == 0 or traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        step += 0.1

    traci.close()
    sys.stdout.flush()
    sumo_subprocess.wait()






