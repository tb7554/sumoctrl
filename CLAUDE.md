# CLAUDE.md

Guidance for AI assistants working on `sumoctrl`. Read this first before making
changes or answering questions about the codebase.

## What this is

`sumoctrl` is a Python library that extends **SUMO** (Simulation of Urban
Mobility) with higher-level control logic for research. It was originally built
to study decentralised algorithms but is designed to accommodate centralised
control and macroscopic-flow calculations as well. Two problem domains drive
the design:

1. Vehicle routing algorithms (`routes/`)
2. Intersection / traffic-light control algorithms (`intersections/`)

The high-level data flow is:

```
.net.xml  -> sumolib.net.readNet   -> road_network_object
road_network_object + traci subscriptions -> sumoctrl controllers
controllers  <->  traci  <->  sumo / sumo-gui
```

`sumolib` parses the network file into Python objects; `traci` is the live
control API. `sumoctrl` sits on top and orchestrates both.

## Repository layout

```
sumoctrl/
├── README.txt                    # Original short design notes (see header here first)
├── __init__.py                   # Empty; repo root doubles as the top-level package
├── create/                       # Placeholder. Intended: scaffold new simulation
│                                 # directories from scratch. Currently only __init__.py.
├── interface/
│   └── getdata.py                # TraCI subscription wrappers:
│                                 #   SumoSubscription, LaneSubscription, VehSubscription
├── intersections/                # Core of the project (most working code lives here)
│   ├── controlled_intersection_container.py
│   │   └── BasicIntersectionContainer — owns a shared LaneSubscription
│   │     and dispatches per-step updates to member intersections.
│   ├── sumo_intersection_interface.py
│   │   └── IntersectionControllerInterface — per-intersection state:
│   │     incoming/outgoing lanes, link_index <-> lane maps, stage matrix,
│   │     current stage, queue lengths.
│   ├── extract_intersection_topology.py
│   │   └── IntersectionTopology — reads a .net.xml (with programs +
│   │     connections) and builds lane/edge/link-index lookup dicts for
│   │     every node in the network (TLS and non-TLS).
│   ├── extract_tls_logic.py
│   │   └── network_tls_logic — dict- and numpy-matrix representations
│   │     of stages + compatible-phase matrices for TLS nodes only.
│   └── propogating_pressure_intersection_simulation.py
│       └── End-to-end example: runs sumo-gui, applies a propagating-
│         pressure max-pressure-style TLS controller each green cycle.
├── plot/                         # Matplotlib helpers for formatted publication plots
│   └── (functions live in plot/__init__.py: get_formatted_plot, format_plot_axis)
├── routes/                       # Placeholder for vehicle-routing algorithms.
├── runsim/
│   └── launch_sumo_process()     # Spawn sumo/sumo-gui via subprocess and init TraCI.
├── utils/
│   └── save_obj / load_obj       # pickle helpers
│       get_open_port             # free TCP port for TraCI
│       add_sumo_tools_to_path    # append $SUMO_HOME/tools to sys.path
└── test/
    ├── test_interface.py         # Runnable smoke script (not pytest-style).
    └── test_scenario/            # Small self-contained SUMO scenario
                                  # (test.sumocfg + net + routes) used by test_interface.py.
```

Most subpackages have a docstring-style module header with author (Tim Barker)
and date — preserve that style when adding new files.

## Conventions

- **Python 2 / 3 compatibility.** Source uses `from __future__ import
  print_function, division`. Keep `print(...)` calls and avoid bare `print`
  statements when editing.
- **Absolute imports rooted at the repo.** Modules import siblings as
  `from interface import getdata`, `from utils import ...`, `from runsim
  import launch_sumo_process`, `from intersections.extract_intersection_topology
  import IntersectionTopology`. Scripts must therefore be run with the repo
  root on `PYTHONPATH` (usually by running from that directory). Do not
  convert these to relative `from .x import y` imports without reason — it
  breaks the `if __name__ == "__main__"` entry points.
- **SUMO_HOME discovery.** The canonical pattern is
  `utils.add_sumo_tools_to_path()`, which appends `$SUMO_HOME/tools` to
  `sys.path` (or exits if `SUMO_HOME` is unset). Call it *before* `import
  traci` or `from sumolib import net`. Several older files still do this
  inline (and even `os.environ['SUMO_HOME'] = '/sumo'` at module scope —
  see `extract_intersection_topology.py`, `extract_tls_logic.py`,
  `propogating_pressure_intersection_simulation.py`). Prefer the utils
  helper in new code.
- **Naming.** Long, descriptive, snake_case names that encode semantics
  (e.g. `network_intersection_input_lane_to_output_edge_to_link_index_dict`).
  Matching `_dict` / non-suffixed variants often coexist: dict keyed by
  id *and* an ordered list aligned with `self._network_intersection_ids`.
  Preserve both when extending.
- **Link indices.** A "link index" identifies a specific movement
  (in-lane, out-edge) at an intersection and is the primary key for
  queues, phases, and TLS stage strings. Keep `in_lane_and_out_edge_to
  _link_index` and inverse mappings in sync.
- **TLS stage strings.** Characters follow SUMO convention: `G` (priority
  green), `g` (permissive green / give-way), `r` (red), `y` (amber).
  `stages_to_compatible_phases_matrix` maps `r→0`, `g→giveway_value`
  (default 1), `G→1`. `get_intersection_amber_phase_strings` builds the
  transitional amber string between two green stages.
- **TraCI subscriptions.** Prefer subscribing through
  `interface.getdata.LaneSubscription` / `VehSubscription` over direct
  per-step `traci.lane.getXxx` calls — the container pattern in
  `BasicIntersectionContainer` assumes a single shared subscription that
  is refreshed once per step.
- **Pickle for caching.** Expensive topology objects are typically saved
  with `utils.save_obj` / `load_obj` (name is given without `.pkl`).

## Running simulations

There is no package manager config, no `setup.py`, no `requirements.txt`,
no test runner wiring. Everything depends on:

- Python with `numpy` and `matplotlib`
- A working SUMO install with `$SUMO_HOME` exported so `sumolib` and
  `traci` are importable from `$SUMO_HOME/tools`
- `sumo` / `sumo-gui` on `$PATH`

Typical entry-point pattern (see `test/test_interface.py`):

```python
from utils import get_open_port, add_sumo_tools_to_path
from runsim import launch_sumo_process
from interface import getdata

add_sumo_tools_to_path()
import traci

port = get_open_port()
proc = launch_sumo_process("path/to/scenario.sumocfg", port,
                           sumo_binary="sumo-gui", gui_on=False)

lane_sub = getdata.LaneSubscription()
lane_sub.activate_subscription()           # defaults to all lanes, LAST_STEP_VEHICLE_ID_LIST

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    lane_sub.update_subscription_with_sumo()
    results = lane_sub.retrieve_subscription_results()

traci.close()
proc.wait()
```

Run from the repository root so the top-level package imports resolve:

```
cd /path/to/sumoctrl
python test/test_interface.py
```

The `test/` directory holds *runnable demo/smoke scripts*, not pytest
unit tests. There is no `pytest` / `unittest` suite — "running the tests"
means executing these scripts and watching SUMO complete.

## Known rough edges (do not silently "fix" — confirm with user first)

Several files were committed as works-in-progress. When touching them,
flag rather than quietly rewrite:

- `intersections/controlled_intersection_container.py:41` — `for
  intersection in self._id2intersection.values()` is missing the
  trailing colon; the module will not import as-is.
- `intersections/sumo_intersection_interface.py` — `IntersectionController
  Interface.__init__` reads `self._id` / `self._num_queues` / etc. before
  assigning them, and references `traci` without importing it. It is a
  scaffold for the intended interface, not runnable code.
- `intersections/propogating_pressure_intersection_simulation.py` —
  `import tls_logic` refers to a module not present in the repo; hard-codes
  `/Users/tb7554/...` paths and `os.environ['SUMO_HOME'] = '/sumo'`; uses
  `traci.trafficlights` (deprecated; newer SUMO uses `traci.trafficlight`).
- `extract_intersection_topology.py` / `extract_tls_logic.py` also set
  `os.environ['SUMO_HOME'] = '/sumo'` at import time, which will override
  the user's real `SUMO_HOME`.
- Filename typo: `propogating_pressure_intersection_simulation.py`
  (should be "propagating"). Keep the existing spelling unless the user
  asks for a rename; other files/commits reference it.
- `create/__init__.py`, `routes/__init__.py`, `intersections/__init__.py`,
  and `runsim/__init__.py` (partly) are empty placeholders.

## Git workflow

- Default branch: `master`.
- Current feature branch for documentation work:
  `claude/add-claude-documentation-5hgcf`.
- Commit style observed in history is a single descriptive sentence or
  paragraph — no conventional-commits prefixes. Match the existing tone
  ("Added X and ...", "Updated to ...", "Created X ...").
- Do not create pull requests unless explicitly asked.

## When editing

- Read the target file first; many modules share long parallel dict/list
  data structures that must stay aligned.
- Preserve the module header docstring block (`@file`, `@author`,
  `@date`). Update the date when doing substantive edits.
- Keep `from __future__` imports at the top of any file that already
  uses them.
- If you add a new module that talks to SUMO, call
  `utils.add_sumo_tools_to_path()` before `import traci` / `from sumolib
  import net`, and do not hard-code `SUMO_HOME`.
- Prefer extending the subscription classes in `interface/getdata.py`
  over adding ad-hoc `traci.*.getXxx` loops inside controllers.
