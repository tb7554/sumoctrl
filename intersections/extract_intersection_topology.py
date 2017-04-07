# #!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@file   intersections/extract_intersection_topology.py
@author  Tim Barker
@date    24/03/2017

Files for extracting the traffic light logic from the sumo net file. These can then be used by the intersection objects.

"""
import os, sys, copy

import numpy as np

os.environ['SUMO_HOME'] = '/sumo'

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import net
from collections import defaultdict

def sumo_net_object_wrapper(func):
    def func(*args):
        netobj = net.readNet(args[0], withPrograms=True, withConnections=True)
        return func(netobj)
    return func

class IntersectionTopology():
    """Container class for intersection topology. Intersection objects store topology for all intersections in 
        the network. tls objects store topology only for traffic light controlled intersections."""

    def __init__(self, netfile_filepath):
        netobj = net.readNet(netfile_filepath, withPrograms=True, withConnections=True)

        self._network_intersection_ids = []
        self._network_tls_ids = []

        self._network_intersection_input_lanes_to_indices_dict = None
        self._network_intersection_output_lanes_to_indices_dict = None
        self._network_intersection_output_edge_to_indices_dict = None
        self._network_intersection_input_lane_to_output_edge_to_link_index_dict = None

        # Copying the dicts into an ordered array for mapping functions
        self._network_intersection_input_lanes_to_indices = None
        self._network_intersection_output_lanes_to_indices = None
        self._network_intersection_output_edge_to_indices = None
        self._network_intersection_input_lane_to_output_edge_to_link_index = None

        # Run set method
        self.set_intersection_in_and_out_lanes_and_ids(netobj)
        self.set_input_lane_to_output_edge_to_link_index_dict()

    def set_intersection_in_and_out_lanes_and_ids(self, net_obj):

        network_intersection_input_lanes = {}
        network_intersection_output_lanes = {}
        network_intersection_output_edges = {}
        network_intersection_in_lane_to_out_lane = defaultdict()

        # For all intersections get the input lanes, output lanes and output edges
        for intersection in net_obj.getNodes():

            if intersection._type != 'traffic_light':

                intersec_id = intersection.getID()
                self._network_intersection_ids.append(intersec_id)
                in_lanes = []
                out_lanes = []
                out_edges = []
                for in_edge in intersection.getIncoming():
                    for in_lane in in_edge._lanes:
                        for connection in in_lane._outgoing:

                            in_lanes.append(connection._fromLane.getID()) # Append the input lane
                            out_lanes.append(connection._toLane.getID()) # Output lane
                            out_edges.append(connection._to.getID()) # Output edge

                network_intersection_input_lanes.update({intersec_id: in_lanes})
                network_intersection_output_lanes.update({intersec_id: out_lanes})
                network_intersection_output_edges.update({intersec_id: out_edges})

        # Repeat the same process for only the traffic light controlled intersections
        tls_in_lanes = {}
        tls_out_lanes = {}
        tls_out_edges = {}

        for tls in net_obj._tlss:

            tls_id = tls.getID()
            self._network_intersection_ids.append(intersec_id)
            self._network_tls_ids.append(tls_id)

            in_entry = ['__' for conn in tls._connections]
            out_entry = ['__' for conn in tls._connections]
            out_edge = ['__' for conn in tls._connections]

            for conn in tls._connections:
                in_entry[conn[2]] = conn[0].getID()
                out_entry[conn[2]] = conn[1].getID()
                out_edge[conn[2]] = conn[1]._edge.getID()

            tls_in_lanes.update({tls_id: in_entry})
            tls_out_lanes.update({tls_id: out_entry})
            tls_out_edges.update({tls_id: out_edge})

        network_intersection_input_lanes.update(tls_in_lanes)
        network_intersection_output_lanes.update(tls_out_lanes)
        network_intersection_output_edges.update(tls_out_edges)

        # Assign new lists as dictionaries
        self._network_intersection_input_lanes_to_indices_dict = network_intersection_input_lanes

        self._network_intersection_output_lanes_to_indices_dict = network_intersection_output_lanes

        self._network_intersection_output_edge_to_indices_dict = network_intersection_output_edges

        # Put into ordered lists so they can be using in map functions later on
        self._network_intersection_input_lanes_to_indices = [network_intersection_input_lanes[intersection_id]
                                                             for intersection_id in self._network_intersection_ids]

        self._network_intersection_output_lanes_to_indices = [network_intersection_output_lanes[intersection_id]
                                                              for intersection_id in self._network_intersection_ids]

        self._network_intersection_output_edge_to_indices = [network_intersection_output_edges[intersection_id]
                                                             for intersection_id in self._network_intersection_ids]


    def set_input_lane_to_output_edge_to_link_index_dict(self):

        network_intersection_link_index_by_in_lane_and_out_edge = defaultdict(dict)

        for intersection_index, intersection_input_lanes in enumerate(
                self._network_intersection_input_lanes_to_indices):

            intersection_link_index_by_in_lane_and_out_edge = defaultdict(defaultdict)

            intersection_id = self._network_intersection_ids[intersection_index]

            for link_index, input_lane in enumerate(intersection_input_lanes):

                output_edge = self._network_intersection_output_edge_to_indices[intersection_index][link_index]

                intersection_link_index_by_in_lane_and_out_edge[input_lane][output_edge] = link_index
                network_intersection_link_index_by_in_lane_and_out_edge[intersection_id] = intersection_link_index_by_in_lane_and_out_edge

        self._network_intersection_input_lane_to_output_edge_to_link_index_dict = network_intersection_link_index_by_in_lane_and_out_edge

        self._network_intersection_input_lane_to_output_edge_to_link_index = [
            network_intersection_link_index_by_in_lane_and_out_edge[intersection_id]
            for intersection_id in self._network_intersection_ids]

    def get_network_intersection_ids(self):
        return copy.deepcopy(self._network_intersection_ids)

    def get_network_intersection_input_lanes(self):
        return copy.deepcopy(self._network_intersection_input_lanes_to_indices_dict)

    def get_network_intersection_output_lanes(self):
        return copy.deepcopy(self._network_intersection_output_lanes_to_indices_dict)

# Get all the incoming lanes of the intersection
# Outgoing edge will be gotten from vehicle at the front of the lane
# Incoming lanes and outgoing edges will be enough to forward pressures on
# node -> _outgoing -> _incoming -> edge -> 0 (connection) -> _direction, _fromLane, _toLane

if __name__ == "__main__":

    netfile_filepath = "/Users/tb7554/PyCharmProjects/_654_Luxembourg_/Net_XML_Files/LuSTScenario.net.xml"

    it = IntersectionTopology(netfile_filepath)



