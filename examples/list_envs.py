# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
# 
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: An execution program for listing the IP
# =============================================================================
import os
import sys

# Taken from https://docs.python-guide.org/writing/structure/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.swarm import SWARM

sim_manager = SWARM()

# This has to run first, so we can download the Supported Environments
sim_manager.retreive_supported_environments()

# Then, we extract the specific information about the environment we care about
sim_manager.retreive_environment_information("SWARMHome")

# TODO Print out what was received
