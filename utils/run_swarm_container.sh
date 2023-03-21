#! /bin/bash

# This file runs the Docker container with required networking ports so that
# the SWARM system can function. This also creates a cache directory for
# offline validation of License Keys, which is mounted into the container
# at runtime.

if [ -d ".cache" ]:
then
    echo "Directory .cache exists."
else
    echo "Creating .cache directory"
    $_mkdir -p ".cache"
fi

docker run -it --rm --gpus=all --runtime=nvidia --network=host -v $pwd.cache:/home/airsim_user/SWARMCore/core/.cache $1