# ===============================================================
# Copyright 2022. Codex Laboratories LLC
# Created By: Tyler Fedrizzi
# Authors: Tyler Fedrizzi
# Created On: July 14th, 2022
# Updated On: July 14th, 2022
# 
# Description: Base class and utilities for building and designing
#              algorithms.
# ===============================================================
import inspect
import importlib
import traceback

from .data_classes import AccVec3, GPSPosVec3, PosVec3, Quaternion, VelVec3, AgentState, Trajectory

PRECISION = 4


class Algorithm():
    """
    Base algorithm class utilized to provide common features and memory
    space to individual algorithms.

    ## Inputs:
    - None
    """
    def __init__(self):
        # TODO Add in a "Debug" mode to check memory usage
        self.maximum_memory = 500.0  # Megabytes
        self.current_memory = 0.0  # Megabytes
        self.position = PosVec3()
        self.gps_position = GPSPosVec3()
        self.linear_velocity = VelVec3()
        self.angular_velocity = VelVec3()
        self.linear_acceleration = AccVec3()
        self.angular_acceleration = AccVec3()
        self.orientation = Quaternion()
        self.RPY = [float(), float(), float()]
        self.heading = float()
        self.swarm_states = list()
        self.received_messages = list()
        self.states = list()
        self.use_states = False
        self.current_state = "initialize"
        self.coordinate_frame = "NED"
        self.memory = SystemMemory()
        self.goal = PosVec3()
        self.trajectory = Trajectory()
        self.input_mapping = {
            "Position": self.position,
            "GPSPosition": self.gps_position,
            "LinearVelocity": self.linear_velocity,
            "AngularVelocity": self.angular_velocity,
            "AngularAcceleration": self.angular_acceleration,
            "Heading": self.heading,
            "Orientation": self.orientation,
            "SwarmState": self.swarm_states,
            "Messages": self.received_messages,
            "Memory": self.memory,
            "Trajectory": self.trajectory,
            "Goal": self.goal
        }
        self.agent_id = None

    def update_agent_state(self, agent_state: AgentState) -> None:
        """
        Given the current state of the system, update the attributes
        to provide current information to the Algorithm.

        ## Input:
        - agent_state [AgentState] compact class containing required
                                   state information for completing
                                   obstacle avoidance
        
        ## Outputs:
        - None
        """ 
        if self.coordinate_frame == "ENU":
            self.position = agent_state.position.toENU()
            self.gps_position = agent_state.gps_position
            self.linear_velocity = agent_state.linear_velocity.toEnu()
            self.angular_velocity = agent_state.angular_velocity.toEnu()
            self.linear_acceleration = agent_state.linear_acceleration.toENU()
            self.angular_acceleration = agent_state.angular_acceleration.toENU()
            self.orientation = agent_state.orientation.toENU()
        else:
            self.position = agent_state.position
            self.gps_position = agent_state.gps_position
            self.linear_velocity = agent_state.linear_velocity
            self.angular_velocity = agent_state.angular_velocity
            self.linear_acceleration = agent_state.linear_acceleration
            self.angular_acceleration = agent_state.angular_acceleration
            self.orientation = agent_state.orientation

    def update_swarm_state(self, swarm_states: list) -> None:
        """
        Given a list of swarm states, which contains the AgentState
        objects for each agent in the swarm who transmitted information
        to the agent (or newest information at any one time), update the
        current "swarm_states" to reference these new updates.

        ## Inputs:
        - swarm_states [list[AgentState]] A list of AgentStates,
          referring to the current state of the Agents.
        
        ## Outputs:
        - None
        """
        self.swarm_states = swarm_states

    def update_received_messages(self, received_messages: list) -> None:
        """
        Received a list of dict objects containing the information
        that was passed from any agent to the current agent.

        ## Inputs:
        - received_messages [list] A list of dict messages in the format
        as follows below.

        Example Message:
        {"timestamp": datetime.datetime(2022, 8, 6, 12, 26, 43, 619426),
         "message": {"YOUR MESSAGE HERE": "YOUR MESSAGE"}}
        
        ## Outputs:
        - None
        """
        self.received_messages = received_messages

    def load_states(self, states: list, module_name: str) -> None:
        """
        Given a set of states and a name for the module to load, load
        the state functions.

        TODO Set up behavior graph in the future to manage transitioning
        between these states.

        ## Inputs:
        - states [list] A list of state names from the user
        - module_name [str] The module that the algorithm will run in

        ## Outputs:
        - None
        """
        try:
            task_module = importlib.import_module("user_code.{}".format(module_name))
        except Exception:
            traceback.print_exec()
            exit("Can't import")

        state_methods = dict()
        members = inspect.getmembers(task_module)

        for state in states:
            func = filter(lambda x: x[0] == (state.lower()), members)
            func = list(func)

            if len(func) == 0:
                exit(0)
            else:
                state_methods[state] = func[0][1]

        self.states = state_methods
        self.use_states = True

    def load_input_args(self, input_arg_keys: list) -> list:
        """
        Given the algorithms input argument list, grab the memory
        references from the Algorithm object and return that to be
        input to the users method.

        ## Inputs:
        - input_arg_keys [list] The list of arguments needed for the
                                current state.
        
        ## Output:
        - A list of memory references containing the data requested by
          the user.
        """
        args = list()
        for arg in input_arg_keys:
            args.append(self.input_mapping[arg])

        return args


    def run(self):
        raise NotImplementedError("Please implement this method!")


class SystemMemory():
    """
    Container object for the memory variables that the User wishes to
    hold on during the life the of Algorithm. Meant as way to track and
    report memory through the life of an algorithm.
    """
    def __init__(self):
        pass

    def store(self, member_name: str, member_object) -> bool:
        try:
            self.__setattr__(member_name, member_object)
        except Exception:
            return False

        return True

    def retrieve(self, member_name) -> object:
        try:
            return self.__getattribute__(member_name)
        except Exception:
            assert KeyError("This attribute does not exist!")

    def calculate_storage_size(self) -> float:
        assert NotImplementedError("Build this method")