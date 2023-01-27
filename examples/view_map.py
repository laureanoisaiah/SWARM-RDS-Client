# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
# 
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: Core Execution of the forward-facing gui
# =============================================================================
import argparse

from core.swarm import SWARM

SIMULATION_NAME = "example"


argpaser = argparse.ArgumentParser("SWARM Simulation Platform",
                                   usage="Run a simulation using a specific map name.",
                                   description="This system represents the client in the SWARM simulation platform. This connects to the core SWARM platform and manages the processing of running a simulation.")
argpaser.add_argument("--map-name", default="SWARMHome", help='The name of the environment to run. Use `list_envs.py` to see which environments are supported')
argpaser.add_argument("--ip-address", default="127.0.0.1", help='The remote IP address of the SWARM Server provided by Codex Labs')

args = argpaser.parse_args()

sim_manager = SWARM(ip_address=args.ip_address)

sim_manager.setup_simulation(args.map_name)

print("Finished!")