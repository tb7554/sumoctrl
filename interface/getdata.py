# #!/usr/bin/env python
"""
@file   interface/getdata.py
@author  Tim Barker
@date    15/04/2026

TraCI subscription wrappers. The container pattern in
intersections.controlled_intersection_container.BasicIntersectionContainer
assumes a single shared subscription refreshed once per simulation step.
"""
from typing import Any, Iterable

from utils import add_sumo_tools_to_path

add_sumo_tools_to_path()

import traci
import traci.constants as tc


class SumoSubscription:

    def __init__(self, subscription_type: str) -> None:
        """Takes subscription type as argument (e.g. 'lane'). Initialises
        the class by retrieving the subscribe command from TraCI for the
        relevant subscription type. Must be activated with `variable_ids`
        using the activate_subscription function. Values are retrieved by
        calling retrieve_subscription_results."""
        self.subscription_type: str = subscription_type
        self._subscription_function = getattr(traci, subscription_type).subscribe
        self._getsubscription_function = getattr(traci, subscription_type).getSubscriptionResults
        self._subscription_results: dict[str, Any] | None = None

    def activate_subscription(self, subscribe_to: str, variable_ids: int | Iterable[int]) -> None:

        if not isinstance(variable_ids, list):
            var_ids_as_tuple: tuple[int, ...] = (variable_ids,)  # type: ignore[assignment]
        else:
            var_ids_as_tuple = tuple(variable_ids)

        self.subscription_function(subscribe_to, varIDs=var_ids_as_tuple)

    def update_subscription_with_sumo(self) -> None:
        self._subscription_results = self._getsubscription_function()

    def retrieve_subscription_results(self) -> dict[str, Any] | None:
        return self._subscription_results


class LaneSubscription(SumoSubscription):

    def __init__(self) -> None:
        SumoSubscription.__init__(self, 'lane')

    def activate_subscription(
        self,
        subscribe_to: str | list[str] = 'all',
        variable_ids: int | Iterable[int] = (tc.LAST_STEP_VEHICLE_ID_LIST,),
    ) -> None:

        if not isinstance(variable_ids, list):
            var_ids_as_tuple: tuple[int, ...] = (variable_ids,)  # type: ignore[assignment]
        else:
            var_ids_as_tuple = tuple(variable_ids)

        if subscribe_to == 'all':
            [self.subscription_function(lane, varIDs=var_ids_as_tuple) for lane in traci.lane.getIDList()]
        else:
            [self.subscription_function(lane, varIDs=var_ids_as_tuple) for lane in subscribe_to]


class VehSubscription(SumoSubscription):

    def __init__(self) -> None:
        SumoSubscription.__init__(self, 'vehicle')
