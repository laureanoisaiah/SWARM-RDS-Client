# SWARM Developer Client
API Library for interacting with the SWARM Simulation Developer system
  
## Additional Documentation
Please view the additional documentation at [SWARM Developer Documentation](https://codexlabsllc.github.io/SWARMSimFirmware/)
  
## Dependencies
Supported Versions of Python: 3.7 - 3.11
Supported SWARM Core Containers: 1.0.0
Python Dependencies:
- Matplotlib [version >= 3.6]
- tqdm [version >= 4.64]
- Numpy [version >= 1.22]

## Getting Started
First, ensure that you have installed the dependencies as listed in
the `requirements.txt` folder. This can be installed with `python3 -m pip install -r requirements.txt`.
  
## Installing the License File
You will need a License to run the SWARM system. To start, please go to your
welcome email and have that open.
  
Next, create a file called `LicenseKey.json` in the `settings` folder and ensure it has the following
layout, with the key and account id provided in the welcome email:
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
  
Next, you will need to install the SWARM Core system **only** if you are using
the local edition of the software. If you are on the cloud, you can skip down to
[Running A Simulation - Cloud](#running-a-simulation---cloud).
  
## Installing SWARM Core (Local Only)
You will be provided with a tar file that contains the SWARM Core system,
which is a server that manages the entire simulation process.

### Step 1:
For Ubuntu, please follow the instructions to set up `nvidia-docker` here: [Instructions - Linux](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
  
### Step 2:
Please download the tar file that was provided to you in the welcome email,
which will be a Google Drive link.
  
Next, in the same directory where you put the tar file, you will load the container into the Docker engine: `docker load --input TAR_FILE_NAME`.
  
**Note**`TAR_FILE_NAME` refers to the name of the tar file provided.
  
Please be aware that this will take several minutes as the containers are generally very large.
  
### Step 3:
Once the container has been loaded, you can run `docker image list` and you should see the container listed
as the same name as the tar file.
  
### Step 4:
In the `utils` folder of this repository, there is a shell script for running the container. This will
automatically start all services that are neededd to run. You can move this shell script wherever you like.
  
Once you have moved said file, please create a directory in that same place called `.cache` and allow writing
permissions on this folder with `chmod 777 .cache`. This cache allows a small cache to be stored for license keys
and certain metadata that is required to run the system.
  
## Running A Simulation - Local
To begin, if you have a local installation of the SWARM Developer system, you
will be able to quickly get started.
  
First, start the SWARM Core server by running the script `./run_swarm_container.sh` in the same directory where you created the `.cache` folder. You do not need to have a GUI
running to do this (ie. this can be done on a remote server as well).
  
You can run an example simulation by running:
```
python3 main.py --map-name SWARMHome
```
**Note** If you are on Windows, use `python` instead of `python3`.
  
Also, please checkout the examples for other functionality as well in the `examples` folder.
  
To view the visuals, go to any web browser on the same computer and type in `127.0.0.1` once the simulation
is running. Click `Start` and you will now have an interactive simulation, where you can fly around (hit the `m` key and use the arrow keys) 
and you can also open or close doors (hit the `o` key) and turn on the lights (hit the `l` key).

## Running A Simulation - Cloud
Get started in the cloud is even easier. Just ensure that you have this repository
downloaded.
  
Get the ip address from the Codex representative, which will be sent when you
request access to the cloud. Then, you run the system just as you would with a local
install with:
```
python3 main.py --map-name SWARMHome --ip-address IP_ADDRESS
```
**Note** If you are on Windows, use `python` instead of `python3`.

