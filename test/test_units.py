# #!/usr/bin/env python
"""
@file   test/test_units.py
@author  Tim Barker (regression harness added by Claude 2026-04-15)
@date    15/04/2026

Unit tests for sumoctrl modules that do NOT need a live SUMO simulation.

Covers:
  - utils: save_obj/load_obj round-trip, get_open_port, add_sumo_tools_to_path
  - plot:  get_formatted_plot, format_plot_axis smoke
  - interface.getdata: constructors and update/retrieve flow with mocked traci
  - intersections.extract_tls_logic.stages_to_compatible_phases_matrix:
      hand-crafted stage -> compatible-phase matrix

These tests run on the pre-conversion baseline AND after the Py3.10+
conversion; behaviour must match.
"""
from __future__ import print_function

import os
import pickle
import socket
import sys
import tempfile
import types
import unittest.mock as mock

import matplotlib
matplotlib.use("Agg")  # headless backend; must be set before pyplot import

import pytest


# ---------------------------------------------------------------------------
# utils
# ---------------------------------------------------------------------------

def test_save_and_load_obj_round_trip(tmp_path):
    from utils import save_obj, load_obj
    payload = {"a": 1, "b": [2, 3, 4], "c": {"nested": True}}
    name = str(tmp_path / "roundtrip")
    save_obj(payload, name)
    assert os.path.exists(name + ".pkl")
    assert load_obj(name) == payload


def test_get_open_port_returns_bindable_port():
    from utils import get_open_port
    port = get_open_port()
    assert isinstance(port, int)
    assert 1 <= port <= 65535
    # The port should be bindable (no one else has grabbed it in the
    # microseconds since it was released).
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("", port))
    finally:
        s.close()


def test_add_sumo_tools_to_path_appends(monkeypatch, tmp_path):
    import utils
    fake_sumo = tmp_path / "fake_sumo"
    (fake_sumo / "tools").mkdir(parents=True)
    monkeypatch.setenv("SUMO_HOME", str(fake_sumo))
    # Snapshot sys.path so we can assert the function appended the tools dir.
    path_before = list(sys.path)
    utils.add_sumo_tools_to_path()
    assert str(fake_sumo / "tools") in sys.path
    # Leave sys.path in its original state so subsequent tests don't see the
    # fake directory.
    sys.path[:] = path_before


def test_add_sumo_tools_to_path_exits_when_unset(monkeypatch):
    import utils
    monkeypatch.delenv("SUMO_HOME", raising=False)
    with pytest.raises(SystemExit):
        utils.add_sumo_tools_to_path()


# ---------------------------------------------------------------------------
# plot
# ---------------------------------------------------------------------------

def test_get_formatted_plot_returns_axes():
    from plot import get_formatted_plot
    ax = get_formatted_plot(fsize=(2, 2), textsize=6, scale=0.5)
    # The function returns a matplotlib Axes instance (from plt.subplot(111)).
    from matplotlib.axes import Axes
    assert isinstance(ax, Axes)
    # Spines should all be invisible per the function's chartjunk removal.
    for side in ("top", "bottom", "right", "left"):
        assert ax.spines[side].get_visible() is False
    import matplotlib.pyplot as plt
    plt.close("all")


def test_format_plot_axis_runs_without_error():
    from plot import get_formatted_plot, format_plot_axis
    get_formatted_plot(fsize=(2, 2))
    # Should not raise.
    format_plot_axis([0, 1, 2], ["a", "b", "c"], [0, 1], ["x", "y"])
    import matplotlib.pyplot as plt
    plt.close("all")


# ---------------------------------------------------------------------------
# interface.getdata (traci-dependent; we stub traci in)
# ---------------------------------------------------------------------------

def _import_getdata_with_stub_traci():
    """Import interface.getdata, with stubbed traci/traci.constants modules.

    getdata.py calls add_sumo_tools_to_path() at import time then does
    `import traci; import traci.constants as tc`. To keep the test hermetic
    we inject the stubs into sys.modules before (re-)importing.
    """
    # Remove cached imports so stubs take effect.
    for mod in ("interface.getdata", "traci", "traci.constants"):
        sys.modules.pop(mod, None)

    fake_traci = types.ModuleType("traci")
    fake_traci.lane = mock.MagicMock()
    fake_traci.lane.subscribe = mock.MagicMock()
    fake_traci.lane.getSubscriptionResults = mock.MagicMock(return_value={"lane_x": {}})
    fake_traci.lane.getIDList = mock.MagicMock(return_value=["lane_a", "lane_b"])
    fake_traci.vehicle = mock.MagicMock()
    fake_traci.vehicle.subscribe = mock.MagicMock()
    fake_traci.vehicle.getSubscriptionResults = mock.MagicMock(return_value={})

    fake_constants = types.ModuleType("traci.constants")
    fake_constants.LAST_STEP_VEHICLE_ID_LIST = 0x12
    fake_traci.constants = fake_constants

    sys.modules["traci"] = fake_traci
    sys.modules["traci.constants"] = fake_constants

    # getdata imports add_sumo_tools_to_path() at module-import time. Give
    # it a benign SUMO_HOME so it does not sys.exit.
    os.environ.setdefault("SUMO_HOME", tempfile.gettempdir())

    import importlib
    import interface.getdata as getdata  # noqa: E402
    importlib.reload(getdata)
    return getdata, fake_traci


def test_sumo_subscription_init_wires_functions():
    getdata, fake_traci = _import_getdata_with_stub_traci()
    sub = getdata.SumoSubscription("lane")
    assert sub.subscription_type == "lane"
    assert sub._subscription_function is fake_traci.lane.subscribe
    assert sub._getsubscription_function is fake_traci.lane.getSubscriptionResults
    assert sub._subscription_results is None


def test_sumo_subscription_update_and_retrieve():
    getdata, fake_traci = _import_getdata_with_stub_traci()
    sub = getdata.SumoSubscription("lane")
    fake_traci.lane.getSubscriptionResults.return_value = {"lane_x": {0x12: ["v1"]}}
    sub.update_subscription_with_sumo()
    assert sub.retrieve_subscription_results() == {"lane_x": {0x12: ["v1"]}}
    fake_traci.lane.getSubscriptionResults.assert_called_once()


def test_lane_and_veh_subscription_inherit():
    getdata, fake_traci = _import_getdata_with_stub_traci()
    lane_sub = getdata.LaneSubscription()
    assert lane_sub.subscription_type == "lane"
    veh_sub = getdata.VehSubscription()
    assert veh_sub.subscription_type == "vehicle"


# ---------------------------------------------------------------------------
# intersections.extract_tls_logic.stages_to_compatible_phases_matrix
# (pure-python helper, no net file needed)
# ---------------------------------------------------------------------------

def test_stages_to_compatible_phases_matrix_basic():
    # Import via utils path helper to avoid the module's hardcoded SUMO_HOME.
    os.environ.setdefault("SUMO_HOME", tempfile.gettempdir())
    # extract_tls_logic.py sets os.environ['SUMO_HOME'] = '/sumo' at import
    # time on baseline. That's fine for this pure helper; sumolib is only
    # touched by the class __init__.
    from intersections.extract_tls_logic import stages_to_compatible_phases_matrix

    stages = {
        "tls_1": [
            ["G", "G", "r", "r"],   # stage 0: two priority greens
            ["r", "r", "G", "g"],   # stage 1: priority + permissive green
        ],
    }
    result = stages_to_compatible_phases_matrix(stages, giveway_value=1)
    assert result == {
        "tls_1": [
            [1, 1, 0, 0],
            [0, 0, 1, 1],
        ]
    }

    # giveway_value modifier should only affect lowercase 'g'.
    result = stages_to_compatible_phases_matrix(stages, giveway_value=0.5)
    assert result == {
        "tls_1": [
            [1, 1, 0, 0],
            [0, 0, 1, 0.5],
        ]
    }
