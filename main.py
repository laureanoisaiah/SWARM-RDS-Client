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
argpaser.add_argument("--sim-name", default="example", help="A custom name for the simulation you want to use")
argpaser.add_argument("--map-name", default="SWARMHome", help='The name of the environment to run. Use `list_envs.py` to see which environments are supported')
argpaser.add_argument("--ip-address", default="127.0.0.1", help='The remote IP address of the SWARM Server provided by Codex Labs')
argpaser.add_argument("--sim-settings", default="DefaultSimulationSettings", help="The name of the JSON file in the settings folder you wish to use. Dont use `.json`!")
argpaser.add_argument("--trajectory", default="DefaultTrajectory", help="The name of the JSON file in the settings folder that contains a trajectory. Don't use `.json` extensiion!")
argpaser.add_argument("--download-data-only", default="n", help="A flag to determine when you don't want to run a simulation and only collect data")

args = argpaser.parse_args()

sim_manager = SWARM(ip_address=args.ip_address)

if args.download_data_only == "n":
    sim_manager.setup_simulation(args.map_name, settings_file_name="settings/{}.json".format(args.sim_settings))

    new_simulation = sim_manager.build_simulation(args.sim_name, settings_file_name="{}.json".format(args.sim_settings), trajectory_file_name="{}.json".format(args.trajectory))

    try:
        sim_manager.run_simulation(args.map_name, args.sim_name)
    except KeyboardInterrupt:
        pass

answer = input("Would you like to download data? (y/n)")
if answer == "y":
    sim_manager.extract_data(args.sim_name)

print("Run completed!")

# =============================================================================
#                           Validate the License Key
# =============================================================================
# TODO Import the KeyGen API

# =============================================================================
#                           Load Environment Information
# =============================================================================
# TODO Load the different supported maps (Should this be a call to the 
# container to grab the pre-built schematics (?))
# TODO Load the Default User Input

# =============================================================================
#                           Map Input
# =============================================================================
# NOTE An input arg should say whether they recreate a simulation or not
# TODO Spin up the GUI tool for inputting points
# Run the Kvy app that will take the image of the map and show it on the screen
# so that the user can click on it.
# Read in the Default Trajectory File
# Read in the Default User Input file

# Handle an Add Point call back
# Handle the user clicking a point on the screen

# =============================================================================
#                           Simulation Options
# =============================================================================
# TODO Create a section where you either turn on flags for lighting
# TODO Eventually, this should be integrated into the GUI application as well
# and/or the Enterprise version
# TODO Options:
#   1. Path follow algorithm (straight lines, curves, etc)
#   2. Show Video Output (FUTURE: Live Stream to Browser)
#   3. Collection Information (Camera, LiDAR, etc.)

# =============================================================================
#                           Send Simulation
# =============================================================================
# TODO Create the new files and then upload the files via Server calls