# #!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@file   intersections/sumo_intersection_interface.py
@author  Tim Barker
@date    06/03/2017

"""

class IntersectionControllerInterface():

    """Individual intersection class for storing relevant data on each intersection."""

    def __init__(self, tls_id, inc_lanes_by_index, out_lanes_by_index, phase_matrix_by_links_index,
                 phase_strings, link_index_to_turning_direction, in_lane_and_out_edge_to_link_index, amber_phase_length=4):


        # ID of the intersection.
        self._id

        # Static information on queues and lanes
        self._num_queues # Number of individual phases (movement from an input link to an output link)

        self._incoming_lanes # Lanes coming into the intersection
        self._outgoing_lanes # and out

        self._incoming_lanes_by_link_index # Array. Lanes coming into the intersection ordered by the queue index they correspond to
        self._outgoing_lanes_by_link_index # Same for out lanes

        self._link_index_by_incoming_lanes # Inverse of self._incoming_lanes_by_index stored as dict
        self._link_index_by_outgoing_lanes # Same for out lanes

        self._link_index_to_turning_direction # Turning direction of the queue ('l','s','r')

        self._outgoing_lane_conservative_capacities_by_link_index = [int((traci.lane.getLength(lane) / (4 + 2.5))) for lane in
                                                          self._incoming_lanes_by_index]

        # Static information on Traffic Light stages and durations

        self._default_amber_stage_duration # default length of any amber stage

        self._stage_matrix # Possible stages represented numerically (1 for green, 0 for red)
        self._stage_strings # String representation of stages

        # Variables relating to the queues

        self._vehicles_in_incoming_lanes_by_link_index # list of vehicles in each queue, ordered by queue order
        self._incoming_queue_size_by_link_index = [0] * self._num_queues  #  The queue length for each index
        self._outgoing_lane_queue_size_by_link_index = [0] * self._num_queues  # The length of outgoing queues by link index

        # Direct data subscription from SUMO

        self._sumo_lanes_subscription = None

        # Variables relating to the traffic light stage and duration. Used for controlling TraCI.

        self._current_stage_index # Current stage of the traffic light

        self._stage_time_remaining # remaining time for the current stage
        self._stage_status = True # True for green stage, False for an amber stage

    def update_data(self, lanes_to_queues_subscription_data):
        for index, lane in enumerate(self._incoming_lanes_by_index):
            self._vehicles_in_incoming_lanes_by_link_index[index] = lanes_to_queues_subscription_data[lane]

        for index, lane in enumerate(self._outgoing_lanes_by_link_index):
            self._queue_lengths_by_link_index[index] = len(self._vehicles_in_queues[index])






