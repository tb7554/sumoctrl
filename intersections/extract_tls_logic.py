# #!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@file   intersections/extract_tls_logic.py
@author  Tim Barker
@date    06/03/2017

Files for extracting the traffic light logic from the sumo net file. These can then be used by the intersection objects.

"""
import os, sys

import numpy as np

os.environ['SUMO_HOME'] = '/sumo'

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import net
from collections import defaultdict

class network_tls_logic():
    """Class to easily store tls logic extracted from the sumo net file."""

    def __init__(self, net_file, giveway_value=1):

        self._net_obj = net.readNet(net_file, withPrograms=True, withConnections=True)

        # Information stored as dicts, which are simple and less likely to lead mistakes (intersection id can be used
        # each time to access correct data).
        self._tls_stages = stages_as_dict(self._net_obj, clean_stages=True)
        self._compatible_phases = stages_to_compatible_phases_matrix(self._tls_stages, giveway_value=giveway_value)

        # Conversion to numpy arrays which will be more efficient (some users may prefer this implementation).
        # More likely to lead to mistakes, but also opens up options for using map and reduce.
        self._tls_stages_as_numpy_matrix = np.matrix([np.matrix(matrix) for matrix in self._tls_stages.values()])
        self._compatible_phases_as_numpy_matrix = np.matrix([np.matrix(matrix) for matrix in self._compatible_phases.values()])


def stages_as_dict(net_obj, clean_stages=True):
    """Takes a sumo net object and turns it into a dictionary {tls_id : stage settings as matrix}. The clean_stages
     option removes amber lights from all green stages and removes any 'all red' stages."""

    tls_stages = {}

    for TLS in net_obj._tlss:

        tls_id = TLS.getID()

        stages = []
        for program in TLS._programs:
            for stage_settings, _ in TLS._programs[program]._phases:
                if clean_stages:
                    if 'G' in stage_settings or 'g' in stage_settings:
                        ammended_stage_settings = [letter if letter == 'G' or letter == 'g' else 'r' for letter in stage_settings]
                        if ammended_stage_settings not in stages: stages.append(ammended_stage_settings)
                else:
                    stages.append(stage_settings)

        tls_stages.update({tls_id: stages})

    return tls_stages

def stages_to_compatible_phases_matrix(tls_stages, giveway_value=1):
    """Takes a dictionary of stage settings and returns a dictionary with matrices representing which phases (movements)
     are compatible for each stage. The giveway_value is a modifer for any compatible phase which must none-the-less
     giveway (e.g. right turn and straight are often compatible, but right turning drivers must giveway).
     If giveway_value is not given it defaults to 1, which means it won't be treated any differently in the calculations.
     """

    tls_compatible_phases = {}

    for tls_id in tls_stages:
        compatible_phases = []
        for index, stage in enumerate(tls_stages[tls_id]):
            compatible_phases.append([])
            for letter in list(stage):
                if letter == 'r':
                    compatible_phases[index].append(0)
                elif letter == 'g':
                    compatible_phases[index].append(giveway_value)
                elif letter == 'G':
                    compatible_phases[index].append(1)

        tls_compatible_phases.update({tls_id: compatible_phases})

    return tls_compatible_phases

if __name__ == "__main__":

    netfile_filepath = "/Users/tb7554/PyCharmProjects/_654_Luxembourg_/Net_XML_Files/LuSTScenario.net.xml"

    tls = network_tls_logic(netfile_filepath, giveway_value=1)