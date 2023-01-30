#! /bin/bash

# This file runs the Docker container with required networking ports so that
# the SWARM system can function. This also creates a cache directory for
# offline validation of License Keys, which is mounted into the container
# at runtime.

if [ -d ".cache" ]
then
    echo "Directory .cache exists."
else
    echo "Creating .cache directory"
    mkdir -p ".cache"
fi

if [ ! $1 ]
then
    echo "Error! Please give the name of the container to run!"
    echo "The container to run should be provided in the welcome email"
fi

# docker run -it --rm --gpus=all --runtime=nvidia --network=host -v $pwd/.cache:/home/airsim_user/SWARMCore/.cache $1