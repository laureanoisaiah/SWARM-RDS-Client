# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All rights reserved.
#
# Created By: Tyler Fedrizzi
# Created On: 9 June 2022
#
#
# Description: AirSim interface file for the SWARM platform
# =============================================================================
import logging

from datetime import datetime


def create_logger(process_id: str,
                  component_name: str,
                  agent_id: str) -> logging.Logger:
    """
    Create a consistent logger across different components of the system
    which allows for a standard format for all log files in the future.

    ## Inputs:
    - component_name [str] name of process, usually "Drone"
    - process_id [str] __name__ of current process or thread
    - agent_id [str] id of agent from SWARM system
    """
    file_handler = logging.FileHandler(
        "logs/{agent_id}-{component_name}-{date}.log".format(
            agent_id=agent_id,
            component_name=component_name,
            date="{}-{}-{}".format(
                datetime.utcnow().month,
                datetime.utcnow().day,
                datetime.utcnow().year,
            )
    ))
    log = logging.getLogger(agent_id + process_id)
    log.setLevel(logging.INFO)
    log.addHandler(file_handler)

    return log

def log_info(log: logging.Logger,
             message: str,
             message_type: str,
             agent_id: str) -> None:
    """
    Log message at the information level using the SWARM format.

    ## Inputs:
    - log [Logger] the reference to the logger
    - message [str] the message to log
    - message_type [str] the type of message to send from the SWARM log
                         types
    - agent_id [str] unique id of the agent
    """
    log.info("{}|{}|{}|{}".format(
                            datetime.utcnow(),
                            agent_id,
                            message_type,
                            message
                        )
                    )


def log_error(log: logging.Logger,
              message: str,
              message_type: str,
              agent_id: str) -> None:
    """
    Log message at the error level using the SWARM format.

    ## Inputs:
    - log [Logger] the reference to the logger
    - message [str] the message to log
    - message_type [str] the type of message to send from the SWARM log
                         types
    - agent_id [str] unique id of the agent
    """
    log.error("{}|{}|{}|{}".format(
                            datetime.utcnow(),
                            agent_id,
                            message_type,
                            message
                        )
                    )


class UserLogger():
    """
    Class to simplify user logging in algorithms, where they are able
    to log information and then see the output of their messages.
    """
    def __init__(self, log: logging.Logger, agent_id: str) -> None:
        self.logger = log
        self.agent_id = agent_id
        self.message_type = "user_message"        

    def log_message(self, message: str) -> None:
        log_info(self.logger, message, self.message_type, self.agent_id)