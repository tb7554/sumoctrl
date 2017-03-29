# -*- coding: utf-8 -*-
from __future__ import division
import os, sys, subprocess
import numpy as np

os.environ['SUMO_HOME'] = '/sumo'

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

os.environ["SUMO_BINARY"] = "sumo-gui"

from runsim import checkPorts
import tls_logic
import traci
from sumolib import net
from interface import getdata

from collections import defaultdict, Counter

class CustomCounter:

    def __init__(self, items, values):
        self.count = defaultdict(float)
        for index, item in enumerate(items):
            self.count[item] += values[index]

    def __delitem__(self, item):
        try:
            del self.count[item]
        except KeyError:
            return None


def get_first_cars_in_lane_and_lane_queue(network_intersection_ids, network_intersection_lanes):

    network_intersection_first_cars = []
    network_intersection_queue_by_lane = []

    for index, id in enumerate(network_intersection_ids):

        intersection_first_cars = []
        intersection_queue_by_lane = []

        for lane in network_intersection_lanes[index]:
            lane_cars = traci.lane.getLastStepVehicleIDs(lane)
            intersection_queue_by_lane.append(len(lane_cars))
            if lane_cars :
                first_car = lane_cars[-1]
                intersection_first_cars.append(first_car)
            else:
                intersection_first_cars.append(0)

        network_intersection_first_cars.append(intersection_first_cars)
        network_intersection_queue_by_lane.append(intersection_queue_by_lane)

    return network_intersection_first_cars, network_intersection_queue_by_lane

def get_next_edge(veh_id):
    current_edge = traci.vehicle.getRoadID(veh_id)
    route = traci.vehicle.getRoute(veh_id)
    list_indicies = [list_index for list_index, edge in enumerate(route) if edge == current_edge]
    if len(list_indicies) > 1:
        print("Unable to determine next road due to duplicated edge in route. Ignoring vehicle.")
        return 0
    else:
        remaining_route = route[list_indicies[0]:]
        if len(remaining_route) == 1:
            return 0
        else:
            out_edge = remaining_route[1]
            return out_edge

def get_queue_length_per_link_index(network_intersection_lanes, network_intersection_num_queue_indexes, link_index_by_in_lane_and_out_edge):

    network_intersection_queues_by_link_index = []

    for intersection_index, intersection_lanes in enumerate(network_intersection_lanes):
        intersection_queues_by_link_index = [0]*network_intersection_num_queue_indexes[intersection_index]
        veh_link_indexes = []
        for lane_index, lane in enumerate(intersection_lanes):
            veh_ids = traci.lane.getLastStepVehicleIDs(lane)
            new_indexes = [get_veh_link_index(lane, veh, link_index_by_in_lane_and_out_edge) for veh in veh_ids]
            if new_indexes:
                new_indexes_flattened = [item for sublist in new_indexes for item in sublist]
                veh_link_indexes.extend(new_indexes_flattened)
        index_count = Counter(veh_link_indexes)
        del index_count[-1]

        for entry in index_count:
            intersection_queues_by_link_index[entry] = index_count[entry]

        network_intersection_queues_by_link_index.append(intersection_queues_by_link_index)

    return network_intersection_queues_by_link_index

def get_queue_length_per_link_index_ranked(network_intersection_lanes, network_intersection_num_queue_indexes, link_index_by_in_lane_and_out_edge):

    network_intersection_queues_by_link_index = []

    for intersection_index, intersection_lanes in enumerate(network_intersection_lanes):
        intersection_queues_by_link_index = [0]*network_intersection_num_queue_indexes[intersection_index]
        veh_link_indexes = []
        veh_link_index_importance = []
        for lane_index, lane in enumerate(intersection_lanes):
            veh_ids = traci.lane.getLastStepVehicleIDs(lane)
            new_indexes = [get_veh_link_index(lane, veh, link_index_by_in_lane_and_out_edge) for veh in veh_ids]
            index_value = [1/(len(veh_ids)-index) for index in range(len(veh_ids))]

            if new_indexes:
                new_indexes_flattened = [item for sublist in new_indexes for item in sublist]
                veh_link_indexes.extend(new_indexes_flattened)
                veh_link_index_importance.extend(index_value)
        index_count = CustomCounter(veh_link_indexes, veh_link_index_importance)
        del index_count[-1]
        index_count = index_count.count

        for entry in index_count:
            intersection_queues_by_link_index[entry] = index_count[entry]

        network_intersection_queues_by_link_index.append(intersection_queues_by_link_index)

    return network_intersection_queues_by_link_index

def get_veh_link_index(lane_id, veh_id, link_index_by_in_lane_and_out_edge):
    out_edge = get_next_edge(veh_id)
    if out_edge:
        try:
            index = link_index_by_in_lane_and_out_edge[lane_id][out_edge]
            return [index]
        except KeyError:
            for best_lane in traci.vehicle.getBestLanes(veh_id):
                try:
                    index = link_index_by_in_lane_and_out_edge[best_lane[0]][out_edge]
                    return [index]
                except KeyError:
                    pass
            return [-1]
    else:
        return [link_index_by_in_lane_and_out_edge[lane_id].values()[0]]

def get_queue_indices_of_first_vehicles(network_intersection_lanes, network_intersection_first_cars, network_intersection_in_lane_and_out_edge_to_queue_index):

    network_intersection_first_cars_queue_indicies = []

    for intersection_index, intersection_first_cars in enumerate(network_intersection_first_cars):

        intersection_first_cars_queue_indicies = []

        for first_car_index, first_car in enumerate(intersection_first_cars):

            in_lane = network_intersection_lanes[intersection_index][first_car_index]

            if first_car:

                out_edge = get_next_edge(first_car)

                try:
                    index = network_intersection_in_lane_and_out_edge_to_queue_index[intersection_index][in_lane][out_edge]
                    intersection_first_cars_queue_indicies.append(index)

                except KeyError:
                    for best_lane in traci.vehicle.getBestLanes(first_car):
                        try:
                            index = network_intersection_in_lane_and_out_edge_to_queue_index[intersection_index][best_lane[0]][out_edge]
                            intersection_first_cars_queue_indicies.append(index)
                        except KeyError:
                            intersection_first_cars_queue_indicies.append(None)
            else:
                intersection_first_cars_queue_indicies.append(None)

        network_intersection_first_cars_queue_indicies.append(intersection_first_cars_queue_indicies)

    return network_intersection_first_cars_queue_indicies

def queue_force_calculation(network_intersection_first_cars_in_lanes, network_intersection_first_cars_out_lanes, network_intersection_queues_by_lane):

    in_lane_to_queues = defaultdict(int)
    in_lane_to_out_lane = defaultdict()

    for intersection_index, intersection_queues_by_lane in enumerate(network_intersection_queues_by_lane):
        for lane_index, queues_by_lane in enumerate(intersection_queues_by_lane):
            in_lane = network_intersection_first_cars_in_lanes[intersection_index][lane_index]
            out_lane = network_intersection_first_cars_out_lanes[intersection_index][lane_index]
            in_queue = queues_by_lane

            if in_queue:
                in_lane_to_queues[in_lane] = in_queue
                in_lane_to_out_lane[in_lane] = out_lane

    force = defaultdict(int)
    for in_lane in in_lane_to_queues:
        force[in_lane] = in_lane_to_queues[in_lane]

    new_force = defaultdict(int)

    for in_lane in in_lane_to_queues.keys():
        lanes_checked = [in_lane]
        out_lane = in_lane_to_out_lane[in_lane]
        while out_lane not in lanes_checked:
            new_force[out_lane] += force[in_lane]
            lanes_checked.append(out_lane)
            new_in_lane = out_lane
            if new_in_lane in in_lane_to_out_lane.keys():
                out_lane = in_lane_to_out_lane[new_in_lane]
            else:
                break
        #print(lanes_checked)

    return new_force

def get_network_intersection_first_car_in_lane_and_out_lane(network_intersection_ids, network_intersection_first_cars_queue_indicies, network_intersection_in_lanes_to_indicies, network_intersection_out_lanes_to_indicies):

    network_intersection_first_cars_in_lanes = [[network_intersection_in_lanes_to_indicies[intersection_index][queue_index]
                                                if queue_index != None
                                                else None
                                                 for queue_index in network_intersection_first_cars_queue_indicies[intersection_index]]
                                                for intersection_index, _ in enumerate(network_intersection_ids)]

    network_intersection_first_cars_out_lanes = [[network_intersection_out_lanes_to_indicies[intersection_index][queue_index]
                                                if queue_index != None
                                                else None
                                                 for queue_index in network_intersection_first_cars_queue_indicies[intersection_index]]
                                                for intersection_index, _ in enumerate(network_intersection_ids)]

    return network_intersection_first_cars_in_lanes, network_intersection_first_cars_out_lanes


def convert_force_to_junction_and_index_tuple(lane_to_force, network_intersection_ids, network_intersection_first_cars_in_lanes, network_intersection_first_cars_queue_indicies):

    junction_and_queue_index_and_force_tuples = []

    for intersection_index, intersection_id in enumerate(network_intersection_ids):

        for lane_index, lane_id in enumerate(network_intersection_first_cars_in_lanes[intersection_index]):

                if lane_id in lane_to_force.keys():
                    force = lane_to_force[lane_id]
                    queue_index = network_intersection_first_cars_queue_indicies[intersection_index][lane_index]
                    if queue_index != None : junction_and_queue_index_and_force_tuples.append((intersection_id, queue_index, force))

    return junction_and_queue_index_and_force_tuples

def add_force_to_queues(network_intersection_ids, network_intersection_queues_by_link_index, junction_and_queue_index_and_force_tuples):

    network_intersection_queues_by_link_index_plus_force = network_intersection_queues_by_link_index[:]

    for entry in junction_and_queue_index_and_force_tuples:
        intersection_id = entry[0]
        intersection_link_index = entry[1]
        intersection_link_index_force = entry[2]

        intersection_index = network_intersection_ids.index(intersection_id)

        network_intersection_queues_by_link_index_plus_force[intersection_index][intersection_link_index] += intersection_link_index_force

    return network_intersection_queues_by_link_index_plus_force

def get_intersection_amber_phase_strings(old_phase, new_phase):

    amber_phase = []

    if old_phase == new_phase:
        amber_phase = new_phase
    else:
        for ii in range(0, len(old_phase)):
            if old_phase[ii] == 'r' and new_phase[ii] == 'r':
                amber_phase.append('r')
            elif old_phase[ii] == 'r' and (new_phase[ii] == 'g' or new_phase[ii] == 'G'):
                amber_phase.append('r')
            elif (old_phase[ii] == 'g' or old_phase[ii] == 'G') and (new_phase[ii] == 'r'):
                amber_phase.append('y')
            elif (old_phase[ii] == 'g') and (new_phase[ii] == 'g'):
                amber_phase.append('g')
            elif old_phase[ii] == 'G' and new_phase[ii] == 'G':
                amber_phase.append('G')
            elif old_phase[ii] == 'g' and new_phase[ii] == 'G':
                amber_phase.append('g')
            elif old_phase[ii] == 'G' and new_phase[ii] == 'g':
                amber_phase.append('G')
            else:
                print("Something wrong in amber phase logic. Old: %s, New: %s" % (old_phase[ii], new_phase[ii]))

    intersection_amber_phase_as_string = "".join(amber_phase)

    return intersection_amber_phase_as_string

def get_network_intersection_amber_phase_strings(network_intersection_ids, network_intersection_previous_phase_strings, network_intersection_next_phase_strings):

    """ Sets the intermediate phase between green times. Returns the phase duration and traffic light string. """
    network_intersection_amber_phase_strings = []

    for intersection_index, intersection_id in enumerate(network_intersection_ids):

        old_phase = list(network_intersection_previous_phase_strings[intersection_index])
        new_phase = list(network_intersection_next_phase_strings[intersection_index])
        amber_phase = []

        if old_phase == new_phase:
            amber_phase = new_phase
        else:
            for ii in range(0, len(old_phase)):
                if old_phase[ii] == 'r' and new_phase[ii] == 'r':
                    amber_phase.append('r')
                elif old_phase[ii] == 'r' and (new_phase[ii] == 'g' or new_phase[ii] == 'G'):
                    amber_phase.append('r')
                elif (old_phase[ii] == 'g' or old_phase[ii] == 'G') and (new_phase[ii] == 'r'):
                    amber_phase.append('y')
                elif (old_phase[ii] == 'g') and (new_phase[ii] == 'g'):
                    amber_phase.append('g')
                elif old_phase[ii] == 'G' and new_phase[ii] == 'G':
                    amber_phase.append('G')
                elif old_phase[ii] == 'g' and new_phase[ii] == 'G':
                    amber_phase.append('g')
                elif old_phase[ii] == 'G' and new_phase[ii] == 'g':
                    amber_phase.append('G')
                else:
                    print("Something wrong in amber phase logic. Old: %s, New: %s" % (old_phase[ii], new_phase[ii]))

        intersection_amber_phase_as_string = "".join(amber_phase)

        network_intersection_amber_phase_strings.append(intersection_amber_phase_as_string)

    return network_intersection_amber_phase_strings

def lane_free_detection(lane, full_indication_position=15, full_indication_speed=1):
    """Checks the position of the last vehicle to enter the lane, and its speed.
    If they are both below a threshold the lane is considered full and a 0 value is returned, otherwise it is 1"""
    vehs = traci.lane.getLastStepVehicleIDs(lane)
    if vehs:
        return (traci.vehicle.getLanePosition(vehs[0]) > full_indication_position or traci.vehicle.getSpeed(vehs[0]) > full_indication_speed)
    else:
        return True

if __name__ == "__main__":

    os.environ['SUMO_HOME'] = "/sumo"

    end_step = 7200
    step_length = 0.1
    green_stage_length = 20 # Steps between computing the force driving each traffic light phase
    amber_stage_length = 4
    counter = green_stage_length # Counters used to track when calculation should be done

    # net file
    net_file = "/Users/tb7554/PyCharmProjects/_618_Smallworld_Debug_/Net_XML_Files/Smallworld-10x10-1-Lane-TLS.net.xml"
    # sumolib net object
    network = net.readNet(net_file, withConnections=True, withPrograms=True)

    # List of ids of the tls intersections in the network
    network_tls_ids = network._id2tls.keys()
    # List of ids of all intersections in the network
    network_intersection_ids = network._id2node.keys()

    # nxn matrix of compatible phases, and phase strings. returned as dictionaries with intersection_ids as keys
    tls_comaptible_phase_matrix, tls_stages = tls_logic.get_compatible_lanes_matrix_and_phases_from_net_file(net_file)
    # translate dicts into lists in order of network_intersection_ids
    # Compatible phases used in the congestion-aware phase calculation
    network_tls_compatible_phases_matrix = [tls_comaptible_phase_matrix[intersection_id] for intersection_id in network_tls_ids]
    # tls stage matrix for all tls intersections as list of lists
    network_tls_stage_matrix = [tls_stages[intersection_id] for intersection_id in network_tls_ids]

    # dictionary of {intersection_id : [in lanes with index equal to link index]}, and same dictinoary but with out lanes
    network_tls_in_lanes_to_indicies_dict, network_tls_out_lanes_to_indicies_dict = tls_logic.get_in_out_lanes_to_index(net_file)

    # convert dictionaries to lists in order of network_intersection_ids
    network_tls_in_lanes_to_indicies = [network_tls_in_lanes_to_indicies_dict[intersection_id] for intersection_id in network_tls_ids]
    network_tls_out_lanes_to_indicies = [network_tls_out_lanes_to_indicies_dict[intersection_id] for
                                         intersection_id in network_tls_ids]

    # list of lists [[lane for every intersection] for every intersection in the network]
    network_tls_in_lanes = [[entry for entry in set(network_tls_in_lanes_to_indicies_dict[intersection_id])] for intersection_id in network_tls_ids]

    # dictionary of {intersection {in_lane: {out_edge : link index}}}
    _, link_index_by_tls_id_in_lane_and_out_edge_dict = tls_logic.get_connection_to_turn_defs(net_file)
    # reordered to be in the same order as network_intersection_ids
    network_tls_in_lane_and_out_edge_to_queue_index = [
        link_index_by_tls_id_in_lane_and_out_edge_dict[intersection_id] for
        intersection_id in network_tls_ids]

    # Construct a dictionary which just gives {in_lane : {out_edge : link_index}}
    # link_index_by_intersection_id_in_lane_and_out_edge values as a list
    in_lane_and_out_edge_to_queue_index_as_list = link_index_by_tls_id_in_lane_and_out_edge_dict.values()
    # create a new dictionary which is a flattened version of link_index_by_intersection_id_in_lane_and_out_edge -> {in_lane : {out_edge : link_index}}
    network_in_lane_and_out_edge_to_queue_index_dict = {}
    for tls_id in network_tls_ids:
        network_in_lane_and_out_edge_to_queue_index_dict.update(link_index_by_tls_id_in_lane_and_out_edge_dict[tls_id])

    # number of queues at each intersection, ordered by network_intersection_ids
    network_tls_num_queue_indexes = [network._id2tls[id]._maxConnectionNo + 1 for id in network_tls_ids]

    # All lanes in the network
    network_lanes = [lane.getID() for intersection in network._nodes for edge in intersection.getIncoming() for lane
                     in edge._lanes]

    traci_port = checkPorts.getOpenPort()
    sumoCommand = (
    "sumo -n /Users/tb7554/PyCharmProjects/_618_Smallworld_Debug_/Net_XML_Files/Smallworld-10x10-1-Lane-TLS.net"
    ".xml -r /Users/tb7554/PyCharmProjects/_618_Smallworld_Debug_/SUMO_Input_Files/Routes/Smallworld-10x10-1-Lane-TLS-CGR-1.10-PEN-0.00-0.rou.xml --remote-port %d --step-length %.2f --time-to-teleport -1"
    % (traci_port, step_length))

    sumoProcess = subprocess.Popen(sumoCommand, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    print("Launched process: %s" % sumoCommand)

    # initialise the step
    step = 0

    # Open up traci on a free port
    traci.init(traci_port)
    print("port opened")

    # Set intial traffic light conditions
    network_intersection_current_stage = [network_tls_stage_matrix[intersection_index][0] for intersection_index, intersection_id in enumerate(network_tls_ids)]
    network_stage = 'green'
    network_stage == 'switch_green_to_amber'

    # run the simulation
    while step < end_step and traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        if step >= 4200:
            pass

        if network_stage == 'green':
            #  Green stage. Increment to the next step. If the counter is at 0 then switch to amber stage.
            counter -= step_length

            if counter <= 0 :

                network_stage = 'switch_green_to_amber'
                counter = amber_stage_length

        elif network_stage == 'switch_green_to_amber':
            #  Green->Amber stage. Calculate the next stage. Workout appropriate amber stage.

            # Get the first car in each lane. Get the queue length of each lane.
            network_intersection_first_cars, network_intersection_queues_by_lane =  \
                get_first_cars_in_lane_and_lane_queue(network_tls_ids, network_tls_in_lanes)

            # Get the queue index of the first car (used to find outgoing edge).
            network_intersection_first_cars_queue_indicies = get_queue_indices_of_first_vehicles(
                network_tls_in_lanes,  network_intersection_first_cars, network_tls_in_lane_and_out_edge_to_queue_index)

            # Get the in and out lanes of the first car in each lane
            network_intersection_first_cars_in_lanes, network_intersection_first_cars_out_lanes = \
                get_network_intersection_first_car_in_lane_and_out_lane(network_tls_ids,
                                                                        network_intersection_first_cars_queue_indicies,
                                                                        network_tls_in_lanes_to_indicies,
                                                                        network_tls_out_lanes_to_indicies)

            # Convert the first cars in lane, the first cars out lanes, and the queues by lane into a calculation of
            # propagating pressures.
            lane_to_force = queue_force_calculation(network_intersection_first_cars_in_lanes,
                                    network_intersection_first_cars_out_lanes, network_intersection_queues_by_lane)


            # Convert the junction and queue index into force tuples, which allow propagating pressures to be
            # assigned to the correct queues in the network.
            junction_and_queue_index_and_force_tuples = convert_force_to_junction_and_index_tuple(lane_to_force,
                network_tls_ids, network_intersection_first_cars_in_lanes, network_intersection_first_cars_queue_indicies)

            # Get the queue length using the ranked queue length algorithm
            network_intersection_queues_by_link_index = get_queue_length_per_link_index_ranked(network_tls_in_lanes,
                network_tls_num_queue_indexes, network_in_lane_and_out_edge_to_queue_index_dict)

            # Add the propagating pressures to the ranked queue lengths
            network_intersection_queues_by_link_index_plus_force = add_force_to_queues(network_tls_ids,
                network_intersection_queues_by_link_index, junction_and_queue_index_and_force_tuples)

            # Detect any lanes which are full
            network_intersection_full_out_lane = [[lane_free_detection(out_lane) for out_lane in intersection] for
                                                  intersection in network_tls_out_lanes_to_indicies]

            # Recalculate compatible phases matrix to account for full out lanes (congestion aware traffic light
            # control)
            resultant_phases = map(np.multiply, network_intersection_full_out_lane, network_tls_compatible_phases_matrix)

            # Calculate total queue lengths for each stage using resultant phases calculation
            total_queue_lengths = map(np.dot, resultant_phases, network_intersection_queues_by_link_index_plus_force)
            total_queue_lengths = [entry.tolist() for entry in total_queue_lengths]

            # Identify phase with max pressure for each tls intersection and change settings on traffic lights
            max_pressure_phase_index = [entry.index(max(entry)) for entry in total_queue_lengths]

            # Store previous stage
            network_intersection_previous_stage = network_intersection_current_stage

            # Set new stage
            network_intersection_current_stage = [network_tls_stage_matrix[ii][max_entry] for ii, max_entry in enumerate(max_pressure_phase_index)]

            # Find the corresponding amber stage
            network_intersection_amber_phase_strings = map(get_intersection_amber_phase_strings,
                                                           network_intersection_previous_stage,
                                                           network_intersection_current_stage)

            # Send new tls settings to SUMO via traci
            [traci.trafficlights.setRedYellowGreenState(intersection_id, "".join(network_intersection_amber_phase_strings[intersection_index])) for
             intersection_index, intersection_id in enumerate(network_tls_ids)]

            # Decremement counter and set stage to amber
            counter -= step_length
            network_stage = "amber"

        elif network_stage == "amber":
            counter -= step_length
            if counter <= 0:
                network_stage = "switch_amber_to_green"
                counter = green_stage_length

        elif network_stage == "switch_amber_to_green":

            [traci.trafficlights.setRedYellowGreenState(intersection_id, "".join(
                network_intersection_current_stage[intersection_index])) for
             intersection_index, intersection_id in enumerate(network_tls_ids)]

            network_stage = "green"
            counter -= step_length

        else:
            print("error in stage logic.")

        step += step_length

    traci.close()
    sys.stdout.flush()

    sumoProcess.wait()