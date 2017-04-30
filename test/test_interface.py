# #!/usr/bin/env python
"""
@file   test/test_interface.py
@author  Tim Barker
@date    30/04/2017

Module for running tests on the functions contained in this package.

"""

import sys
from interface import getdata
from utils import get_open_port, add_sumo_tools_to_path
from runsim import launch_sumo_process

add_sumo_tools_to_path()

import traci

if __name__ == "__main__":

    traci_port = get_open_port()

    sumo_config_file = 'test_scenario/test.sumocfg'

    sumo_subprocess = launch_sumo_process(sumo_config_file, traci_port, sumo_binary="sumo-gui", gui_on=False)

    lane_sub = getdata.LaneSubscription()
    lane_sub.activate_subscription()

    # initialise the step
    step = 0

    # run the simulation
    while step == 0 or traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        step += 0.1

        lane_sub.update_subscription_with_sumo()
        lane_results = lane_sub.retrieve_subscription_results()

    traci.close()
    sys.stdout.flush()
    sumo_subprocess.wait()






