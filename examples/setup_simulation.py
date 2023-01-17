# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
# 
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: An example of setting up the SWARM Simulation Platform to
#              prepare to utilize a simulation.
# =============================================================================
from core.swarm import SWARM

ACCESS_KEY = 'test'

sim_manager = SWARM(access_key=ACCESS_KEY)

sim_manager.setup_simulation()