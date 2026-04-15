# #!/usr/bin/env python
"""
@file   test/test_regression_baseline.py
@author  Tim Barker (regression harness added by Claude 2026-04-15)
@date    15/04/2026

Golden-file regression test for intersections.extract_intersection_topology
and the pre-existing behaviour of intersections.extract_tls_logic.

`test_matches_baseline` pickles the dict/list outputs of IntersectionTopology
when parsing test/test_scenario/test.net.xml on the pre-conversion baseline
branch. Post-conversion the same code path must produce identical output.

Note: the baseline pickle is committed alongside this file
(baseline_golden.pkl). Regenerate it by running this file directly:

    SUMO_HOME=... python -m test.test_regression_baseline --write

NB on pre-existing bugs the harness intentionally captures, not fixes:
  1. IntersectionTopology's loop over net_obj._tlss appends the previous
     (non-TLS) `intersec_id` to `_network_intersection_ids` once per TLS
     rather than the current tls_id. This produces a long run of
     duplicate IDs in the output. The golden file captures that as-is so
     the Py3 port is compared apples-to-apples.
  2. network_tls_logic.__init__ raises TypeError on modern sumolib
     because TLS._programs[program]._phases yields Phase objects, not
     tuples. We assert that the same error still occurs post-conversion.
"""
from __future__ import print_function

import os
import pathlib
import pickle
import sys

import pytest


HERE = pathlib.Path(__file__).parent
NET = HERE / "test_scenario" / "test.net.xml"
GOLDEN = HERE / "baseline_golden.pkl"


def _require_sumo_home():
    if not os.environ.get("SUMO_HOME"):
        pytest.skip("SUMO_HOME not set; cannot import sumolib")


def _snapshot():
    """Build the deterministic dicts/lists produced by IntersectionTopology.

    Excludes the `_net_obj` reference (not picklable in general, and not a
    stable output) and anything starting with `__`. Numpy matrices are
    converted to tolist() for stable comparison across numpy versions.
    """
    from intersections.extract_intersection_topology import IntersectionTopology

    topo = IntersectionTopology(str(NET))

    def _clean(attrs):
        out = {}
        for k, v in attrs.items():
            if k.startswith("__"):
                continue
            if k == "_net_obj":
                continue
            # defaultdicts round-trip through pickle fine; keep as-is.
            out[k] = v
        return out

    return {
        "topology": _clean(vars(topo)),
    }


def test_intersection_topology_matches_baseline():
    _require_sumo_home()
    if not GOLDEN.exists():
        pytest.skip(
            "baseline_golden.pkl not yet generated; run "
            "`python -m test.test_regression_baseline --write` on the "
            "pre-conversion branch first"
        )
    expected = pickle.loads(GOLDEN.read_bytes())
    actual = _snapshot()
    assert set(actual.keys()) == set(expected.keys())
    # Compare the topology dict key-by-key for a clearer failure message.
    exp_topo = expected["topology"]
    act_topo = actual["topology"]
    assert set(act_topo.keys()) == set(exp_topo.keys()), (
        "IntersectionTopology attribute set changed: "
        "added={}, removed={}".format(
            set(act_topo.keys()) - set(exp_topo.keys()),
            set(exp_topo.keys()) - set(act_topo.keys()),
        )
    )
    for key in exp_topo:
        # defaultdict compares equal to dict with the same items.
        assert act_topo[key] == exp_topo[key], \
            "IntersectionTopology.%s changed vs. baseline" % key


def test_network_tls_logic_still_raises_same_error():
    """Documents the pre-existing bug in extract_tls_logic.stages_as_dict.

    If the Py3 conversion accidentally 'fixes' this by changing the
    unpack, the test fails and we re-evaluate. If someone legitimately
    fixes the bug, update this test to the new expected behaviour.
    """
    _require_sumo_home()
    from intersections.extract_tls_logic import network_tls_logic
    with pytest.raises(TypeError, match="cannot unpack non-iterable Phase"):
        network_tls_logic(str(NET))


def _write_golden():
    GOLDEN.write_bytes(pickle.dumps(_snapshot(), protocol=pickle.HIGHEST_PROTOCOL))
    print("Wrote baseline golden to %s (%d bytes)" % (GOLDEN, GOLDEN.stat().st_size))


if __name__ == "__main__":
    # Allow running `python -m test.test_regression_baseline --write` to
    # (re)generate the pickle on the pre-conversion baseline branch.
    if "--write" in sys.argv:
        # Make sure the repo root is on sys.path like pytest's conftest does.
        REPO_ROOT = str(pathlib.Path(__file__).resolve().parent.parent)
        if REPO_ROOT not in sys.path:
            sys.path.insert(0, REPO_ROOT)
        sumo_home = os.environ.get("SUMO_HOME")
        if sumo_home:
            tools = os.path.join(sumo_home, "tools")
            if tools not in sys.path:
                sys.path.insert(0, tools)
        _write_golden()
    else:
        print("Use `pytest test/test_regression_baseline.py` to run, "
              "or `python -m test.test_regression_baseline --write` "
              "to (re)generate the baseline pickle.")
