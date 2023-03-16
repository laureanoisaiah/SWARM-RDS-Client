# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC.
# 
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: Setup the SWARM Sim Firmware for installation
# =============================================================================
exec(open('core/_version.py').read())

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='swarm-sim-firmware',
      version="1.2.0",
      author='Codex Laboratories LLC',
      author_email='tylerfedrizzi@codex-labs-llc.com',
      url="https://codexlabsllc.github.io/SWARMSimFirmware",
      description="SWARM Simulation Firmware",
      long_description="""\
SWARM Simulation Firmware

Frontend client to interact with the SWARM Simulation Firmware system.
""",
      packages=['swarm-sim-firmware'],
      install_requires=['matplotlib', 'tqdm', "py-machineid", "requests"],
      license="Apache Software License",
      classifiers=[
          'Programming Language :: Python :: 3',
          'License :: OSI Approved'],
      )
