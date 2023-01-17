# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
# 
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: An example of retreiving the environment information
#              from the SWARM Core System
# =============================================================================
from core.swarm import SWARM

# Replace this with your provided access key!
ACCESS_KEY = 'test'

sim_manager = SWARM(access_key=ACCESS_KEY)

# If you don't have a list of supported environments in
# settings/SupportedEnvironments.json, you should always run this 
# command first.
sim_manager.retreive_supported_environments()

# Access the environments list
environments = sim_manager.access_environment_list()

# Retireve the information for the first supported environment
sim_manager.retreive_environment_information(environments[0])
