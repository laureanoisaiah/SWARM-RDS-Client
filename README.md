# SWARM Developer Client
API Library for interacting with the SWARM Simulation Developer system

## Dependencies
Supported Versions of Python: 3.7 - 3.11
Supported SWARM Core Containers: 1.0.0
Python Dependencies:
- Matplotlib [version >= 3.6]
- tqdm [version >= 4.64]
- Numpy [version >= 1.22]

## Getting Started
First, ensure that you have installed the dependencies as listed in
the `requirements.txt` folder. This can be installed with `python3 -m pip install requirements.txt`.
  
Next, ensure you have followed directions for setting up the SWARM Core
Container, which will provides a server for utilizing and interacting with the core
simulation system.
### Windows
First, you will need to install NVIDIA Docker on WSL 2: [Instructions](https://docs.docker.com/desktop/windows/wsl/).
  
Next, you will need to load the container with: `COMMAND`.
  
Next, create a file called `LicenseKey.json` in the `settings` folder and ensure it has the following
layout:
```
{
    "Key": "YOUR LICENSE KEY HERE",
    "Activated": false,
    "AccountID": "PROVIDED ACCOUNT ID"
}
```
Please ensure the field `Activated` is set to false, as the licensing system
must validate that the licene has been activated. Setting this to true will
cause your requests to be denied when running simuluations. The `AccountID` will be provided with the License key.
  
## Running A Simulation - Local
To begin, if you have a local installation of the SWARM Developer system, you
will be able to quickly get started.
  
### Running the SWARM Core System
First, you need to run the core system before making any requests. This is platform 
dependent so please following these instructions. (**NOTE** Please be aware we do not support Mac due to graphics card issues)
  
#### Linux
For Ubuntu, please follow the instructions to set up `nvidia-docker` here: [Instructions - Linux](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

An example script has been provided in the root of this project called `main.py`.
Please view this file as an example of how to run a simulation. Other examples are 
provided in the `examples` folder and the documentation is also available at:
[SWARM Developer Documentation](https://codexlabsllc.github.io/SWARMSimFirmware/).
  
You can run an example simulation by running `python3 main.py --map-name SWARMHome`.

## Running A Simulation - Cloud
Get started in the cloud is even easier. Just ensure that you have this repository
downloaded.
  
Get the ip address from the Codex representative, which will be sent when you
request access to the cloud. Then, you run the system just as you would with a local
install with:
```
python3 main.py --map-name SWARMHome --ip-address IP_ADDRESS
```
  
