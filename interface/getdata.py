from __future__ import print_function, division
import numpy as np
import os, sys

os.environ['SUMO_HOME'] = '/sumo'

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
import traci.constants as tc

class SumoSubscription():

    def __init__(self, subscription_type):
        """Takes subscription type as argument (e.g. lane). Initialises the class by retrieving the subscribe
        command from traci for the relevant subscription type. Must be activated with 'variable_ids' using the activate
        subscription function. Values are retrieved by calling the retrieve subscription function."""
        self.subscription_type = subscription_type
        self._subscription_function = getattr(traci, "%s" % subscription_type).subscribe
        self._getsubscription_function = getattr(traci, "%s" % subscription_type).getSubscriptionResults
        self._subscription_results = None

    def activate_subscription(self, subscribe_to, variable_ids):

        if type(variable_ids) != list:
            var_ids_as_tuple = tuple([variable_ids])
        else:
            var_ids_as_tuple = tuple(variable_ids)

        self.subscription_function(subscribe_to, varIDs=var_ids_as_tuple)

    def update_subscription_with_sumo(self):
        self._subscription_results = self._getsubscription_function()

    def retrieve_subscription_results(self):
        return self._subscription_results

class LaneSubscription(SumoSubscription):

    def __init__(self):
        SumoSubscription.__init__(self, 'lane')

    def activate_subscription(self, subscribe_to='all', variable_ids=tuple([tc.LAST_STEP_VEHICLE_ID_LIST])):

        if type(variable_ids) != list:
            var_ids_as_tuple = tuple([variable_ids])
        else:
            var_ids_as_tuple = tuple(variable_ids)

        if subscribe_to == 'all':
            [self.subscription_function(lane, varIDs=var_ids_as_tuple) for lane in traci.lane.getIDList()]
        else:
            [self.subscription_function(lane, varIDs=var_ids_as_tuple) for lane in subscribe_to]

class VehSubscription(SumoSubscription):

    def __init__(self):
        SumoSubscription.__init__(self, 'vehicle')