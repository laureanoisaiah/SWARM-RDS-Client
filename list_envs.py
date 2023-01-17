# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
# 
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: An execution program for listing the IP
# =============================================================================
from core.swarm import SWARM

sim_manager = SWARM("test")

sim_manager.retreive_supported_environments()

sim_manager.retreive_environment_information("SWARMHome")

# TODO Print out what was received
