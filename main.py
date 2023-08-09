# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
# 
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: Core Execution of the forward-facing gui
# =============================================================================
import argparse

from SWARMRDS.core.swarm import SWARM

SIMULATION_NAME = "example"


def return_user_boolean(input: str) -> bool:
    """
    Compare the user input to accepted string values
    """
    return input in ["y", "Y", "yes", "Yes"]


argpaser = argparse.ArgumentParser("SWARM Simulation Platform",
                                   usage="Run a simulation using a specific map name.",
                                   description="This system represents the client in the SWARM simulation platform. This connects to the core SWARM platform and manages the processing of running a simulation.")
argpaser.add_argument("--sim-name", default="example", help="A custom name for the simulation you want to use")
argpaser.add_argument("--map-name", default="SWARMHome", help='The name of the environment to run. Use `list_envs.py` to see which environments are supported')
argpaser.add_argument("--ip-address", default="127.0.0.1", help='The remote IP address of the SWARM Server provided by Codex Labs')
argpaser.add_argument("--sim-settings", default="DefaultSimulationSettings", help="The name of the JSON file in the settings folder you wish to use. Dont use `.json`!")
argpaser.add_argument("--trajectory", default="DefaultTrajectory", help="The name of the JSON file in the settings folder that contains a trajectory. Don't use `.json` extensiion!")
argpaser.add_argument("--download-data-only", default="n", help="A flag to determine when you don't want to run a simulation and only collect data")
argpaser.add_argument("--new_sub", default="n", help="Flag for setting up a new submission, which will run an auto-submission generator from scratch")

args = argpaser.parse_args()

sim_manager = SWARM(ip_address=args.ip_address)

if not return_user_boolean(args.download_data_only):
    if return_user_boolean(args.new_sub):
        sim_manager.setup_simulation(args.map_name, settings_file_name="settings/{}.json".format(args.sim_settings))

    new_simulation = sim_manager.build_simulation(args.sim_name, settings_file_name="{}.json".format(args.sim_settings), trajectory_file_name="{}.json".format(args.trajectory))

    try:
        print("\nRunning {} simulation in the {} environment".format(args.sim_name, args.map_name))
        completed = sim_manager.run_simulation(args.map_name, args.sim_name, ip_address=args.ip_address)
        # Automatically download data if the simulation completed
        if completed:
             sim_manager.extract_data(args.sim_name)
    except KeyboardInterrupt:
        pass

print("Run completed!")