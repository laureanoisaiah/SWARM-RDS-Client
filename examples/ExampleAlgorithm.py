# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
# 
# Created By: Tyler Fedrizzi
# Created On: 11 September 2023
#
# Description: An example algorithm that runs on the SWARM RDS Platform in the
#              High Level Behavior module.
# =============================================================================
from typing import Any

from SWARMRDS.utilities.algorithm_utils import Algorithm
from SWARMRDS.utilities.data_classes import PosVec3, Trajectory
from SWARMRDS.utilities.distance_utils import ned_position_difference


class ExampleAlgorithm(Algorithm):
    """
    An example algorithm that would run in the SWARM RDS Platform,
    enabling you to utilize pre-built modules for advanced autonomy
    development.

    ### Arguements:
    - completed_waypoint_distance [float] The distance from the waypoint
                                          in meters to consider the
                                          waypoint "reached" and to
                                          continue to the next waypoint.
    
    The arguements that are provided are read from the Settings file
    that is generated and submitted by the Client. This value will be
    read in and utilized by what is set. If you forget to set this 
    value, then an error will be thrown.
    """
    def __init__(self, completed_waypoint_distance: float) -> None:
        # Ensure you inherit the methods from the Parent class
        super().__init__()
        # Default trajectory is None if we haven't received our
        # trajectory yet.
        self._trajectory = None
        # When provided, the trajectory will be of class Trajectory
        self._trajectory: Trajectory
        self._completed_waypoint_distance = completed_waypoint_distance  # meters

    def run(self, **kwargs) -> Any:
        """
        Core method that is called each loop of the underlying module.
        This function is provided kew word arguements. The kwargs dict
        is **required** for all algorithms, as this is how any data
        that you select to be input to the algorithm will be passed.

        To parse the kwarg dictionary, do the following:
        ```
        key: str
        value: Any
        for key, value in kwargs.items():
            if key == "PointCloud":
                point_cloud = item
        ```

        Please be aware that the two lines before the for loop are
        typing lines to tell the Python interpreter what data type to
        interpret.

        ## Returns:
        - You must return the items that you wish to broadcast to the
          SWARM system. This can be any of the items listed on the
          following page:
          https://www.codexlabsllc.github.io/SWARM-RDS-Client-Dev/custom_algorithms.html
        - For example, if you want the system to go to a specific
          position in NED space, you would return a PosVec3 object
          from the SWARM RDS classes like so:
          ```
          new_pos = PosVec3(X=1.0, Y=2.0, Z=-2.0)
          return new_pos
          ```
        """
        key: str
        value: Any
        for key, value in kwargs.items():
            if key == "Trajectory":
                self._trajectory = value
        
        # We check if the trajectory is pointing to the None object in
        # memory. You can always return None for any return item in
        # the list, which is considered a non-operation and the loop
        # continues.
        if self._trajectory is None:
            self.log.log_message("No Trajectory provided!")
            return None
        
        next_position, heading, speed = self._find_next_point_on_trajectory()

        # You can always access the log object, which is provided for
        # reference in the following file: SWARMRDS/utilities/log_utils.py
        # with the class name UserLogger
        self.log.log_message("Next Position calculated is: {}".format(next_position))

        return next_position, heading, speed
    
    def _find_next_point_on_trajectory(self) -> PosVec3:
        """
        Find the next point on the Trajectory by measuring where we
        are on the current trajectory.

        ### Inputs:
        - None

        ### Outputs:
        - The next position in the North East Down (NED) space.
        """
        heading = 0.0  # Degrees
        speed = 0.0  # Meters per second
        # Check the length of the trajectory. If we have finished, then
        # just have the vehicle stay where it is.
        if len(self._trajectory.points) == 0:
            return PosVec3(), heading, speed

        # Get the first position still on the list
        # You always have access to the Position of the agent, along with
        # all other data listed in the Algorithm base class. This information
        # is updated at 20 Hz from the State reporting module, which is 
        # always running.
        self.log.log_message("Current Position: {}".format(self.position.displayPretty()))
        next_position = self._trajectory.points[0]  
        self.log.log_message("Next Position on Trajectory: {}".format(self._trajectory.points[0]))
        pos_vec = PosVec3(X=next_position["X"],
                          Y=next_position["Y"],
                          Z=next_position["Z"],
                          frame="global")
        
        if "Heading" in next_position.keys():
            heading = next_position["Heading"]
        if "Speed" in next_position.keys():
            speed = next_position["Speed"]
        # If we are at the origin, push the first point in the trajectory.

        # If we aren't, track our position and determine when to continue
        # down our trajectory.
        pos_diff = ned_position_difference(first_pos=pos_vec,
                                           second_pos=self.position)
        self.log.log_message("Position difference is {} meters".format(pos_diff))
        # If the difference between the next position and our current position
        # is less then our threshold, we want to mark off our current position
        # and then move to our next position.
        if pos_diff < self._completed_waypoint_distance:
            # Only remove the last point from the trajectory if there
            # are 2 or more points
            if len(self._trajectory.points) > 1:
                self._trajectory.points.pop(0)
            position = self._trajectory.points[0]
            new_pos = PosVec3(X=position["X"],
                              Y=position["Y"],
                              Z=position["Z"],
                              frame="global")
            if "Heading" in position.keys():
                heading = position["Heading"]
            if "Speed" in position.keys():
                speed = position["Speed"]
           
            return new_pos, heading, speed
        else:
            return pos_vec, heading, speed