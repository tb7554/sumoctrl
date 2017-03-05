Structure and Purpose

This python library is intended for use with Simulation of Urban Mobility. It extends the API with the following
research in mind:

1. Vehicle routing algorithms
2. Intersection control algorithms

The library was created for simulating decentralised algorithms, but it has been designed with the intention that it can
be used to simulate centralised algorithms, as well as calculate macroscopic flows.

Structure:

sumoctrl.routing

This library relates to the rerouting of vehicles


sumoctrl.intersections

This library relates to the control of traffic lights in the network

PROGRAM STRUCTURE

-- sumolib is the SUMO library packaged with SUMO that reads a network into python object files
-- traci is the SUMO API for interfacing with simulations

input netfile -> sumolib -> output road_network_object

road_network_object -> sumoctrl -> controllers

controllers <-> access traci functions <-> sumo

project: sumoctrl

create
- Create simulations from scratch with a directory structure
-

runsim
- Functions to run simulations on desktop and batch run for bluecrystal cluster

routes
- 

intersections


