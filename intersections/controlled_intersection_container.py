# #!/usr/bin/env python
"""
@file   intersections/controlled_intersection_container.py
@author  Tim Barker
@date    15/04/2026

"""

import numpy as np
from interface import getdata

class BasicIntersectionContainer():
    """Container class for controlled intersections. Methods for adding intersections and running a ubiquitous update method
    for each intersection at every time step. Actions are therefore defined within the intersection class itself."""

    def __init__(self):
        self._ids = []
        self._id2intersection = {}
        self._lane_subscriptions = getdata.LaneSubscription()

    def create_intersection(self):
        intersection(self._lane_subscriptions)

    def add_intersection(self, id, intersection_object):
        self._ids.append(id)
        self._id2intersection.update({id:intersection_object})

    def update_lane_subscription(self):
        self._lane_subscriptions.update_subscription_with_sumo()

    def controlled_intersections_step(self, step):
        self.update_lane_subscription()
        for controlled_intersection in self._id2intersection.values():
            controlled_intersection.step()

    def enable_lanes_subscription(self):

        all_lanes = []

        for intersection in self._id2intersection.values():
            all_lanes.append(intersection._incoming_lanes)
            all_lanes.append(intersection._outgoing_lanes)

        all_lanes = set(all_lanes)

        for lane in all_lanes:
            self._lane_subscriptions.activate_subscription(lane)


if __name__ =='__main__':

    bic = BasicIntersectionContainer()
