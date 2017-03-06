# #!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@file   intersections/sumo_intersection_interface.py
@author  Tim Barker
@date    06/03/2017

"""

import numpy as np

class BasicIntersectionContainer():
    """Container class for controlled intersections. Methods for adding intersections and running a ubiquitous update method
    for each intersection at every time step. Actions are therefore defined within the intersection class itself."""

    def __init__(self):
        self._ids = []
        self._id2intersection = {}

    def add_intersection(self, id, intersection_object):
        self._ids.append(id)
        self._id2intersection.update({id:intersection_object})

    def controlled_intersections_step(self, step):
        for controlled_intersection in self._id2intersection.values():
            controlled_intersection.step()

