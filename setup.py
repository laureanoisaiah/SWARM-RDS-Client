# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
#
# Created By: Tyler Fedrizzi
# Created On: 1 August 2023
#
# Description: Setup File for the SWARM RDS Client core library
# =============================================================================
from setuptools import setup

setup(
    name='SWARMRDS',
    version="1.4.0",
    packages=["SWARMRDS", "SWARMRDS/core", "SWARMRDS/utilities"],
    install_requires=['matplotlib', 'tqdm', "py-machineid", "requests", "pandas", "requests"],
    url="https://codexlabsllc.github.io/SWARM-RDS-Client-Dev/",
    description="SWARM RDS Client",
    long_description="""\
SWARM RDS Client\
"""
)