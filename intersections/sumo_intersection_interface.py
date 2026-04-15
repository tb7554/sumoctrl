# #!/usr/bin/env python
"""
@file   intersections/sumo_intersection_interface.py
@author  Tim Barker
@date    15/04/2026

Per-intersection state + update hook for the container in
controlled_intersection_container.py. The class is a scaffold: the
constructor now wires every self._xxx attribute from its arguments so
downstream code (and BasicIntersectionContainer.enable_lanes_subscription)
can read them, but the queue-mutation logic in update_data is still
research-grade and not exercised by any test.
"""

from utils import add_sumo_tools_to_path

add_sumo_tools_to_path()

import traci


class IntersectionControllerInterface():

    """Individual intersection class for storing relevant data on each intersection."""

    def __init__(self, tls_id, inc_lanes_by_index, out_lanes_by_index, phase_matrix_by_links_index,
                 phase_strings, link_index_to_turning_direction, in_lane_and_out_edge_to_link_index,
                 amber_phase_length=4):

        # ID of the intersection.
        self._id = tls_id

        # Static information on queues and lanes
        self._num_queues = len(inc_lanes_by_index)  # one queue per link index

        # Deduplicated lane lists (an intersection may have the same lane
        # appear at multiple link indices).
        self._incoming_lanes = list(set(inc_lanes_by_index))
        self._outgoing_lanes = list(set(out_lanes_by_index))

        # Link-index-ordered lists (the authoritative mapping).
        self._incoming_lanes_by_link_index = inc_lanes_by_index
        self._outgoing_lanes_by_link_index = out_lanes_by_index

        # Inverse mappings: lane -> link index. Where a lane serves multiple
        # link indices the last one wins (dicts only hold one value per key).
        self._link_index_by_incoming_lanes = {lane: idx for idx, lane in enumerate(inc_lanes_by_index)}
        self._link_index_by_outgoing_lanes = {lane: idx for idx, lane in enumerate(out_lanes_by_index)}

        self._link_index_to_turning_direction = link_index_to_turning_direction

        # Back-of-envelope lane capacity: lane length / (vehicle length + gap).
        # Uses TraCI so a SUMO simulation must be running when this
        # constructor is called.
        self._outgoing_lane_conservative_capacities_by_link_index = [
            int(traci.lane.getLength(lane) / (4 + 2.5))
            for lane in self._incoming_lanes_by_link_index
        ]

        # Static information on Traffic Light stages and durations
        self._default_amber_stage_duration = amber_phase_length

        self._stage_matrix = phase_matrix_by_links_index
        self._stage_strings = phase_strings

        self._in_lane_and_out_edge_to_link_index = in_lane_and_out_edge_to_link_index

        # Variables relating to the queues
        self._vehicles_in_incoming_lanes_by_link_index = [[] for _ in range(self._num_queues)]
        self._incoming_queue_size_by_link_index = [0] * self._num_queues
        self._outgoing_lane_queue_size_by_link_index = [0] * self._num_queues

        # Direct data subscription from SUMO
        self._sumo_lanes_subscription = None

        # Variables relating to the traffic light stage and duration. Used for controlling TraCI.
        self._current_stage_index = 0
        self._stage_time_remaining = 0
        self._stage_status = True  # True for green stage, False for an amber stage

    def update_data(self, lanes_to_queues_subscription_data):
        for index, lane in enumerate(self._incoming_lanes_by_link_index):
            self._vehicles_in_incoming_lanes_by_link_index[index] = lanes_to_queues_subscription_data[lane]

        for index, _ in enumerate(self._outgoing_lanes_by_link_index):
            self._incoming_queue_size_by_link_index[index] = len(
                self._vehicles_in_incoming_lanes_by_link_index[index]
            )
