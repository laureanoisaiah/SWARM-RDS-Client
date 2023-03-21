# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
# 
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: An example of setting up the SWARM Simulation Platform to
#              prepare to utilize a simulation.
# =============================================================================
import os
import sys

# Taken from https://docs.python-guide.org/writing/structure/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.swarm import SWARM

ACCESS_KEY = 'test'

sim_manager = SWARM(access_key=ACCESS_KEY)

sim_manager.setup_simulation()