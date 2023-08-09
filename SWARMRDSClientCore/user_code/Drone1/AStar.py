# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All rights reserved.
#
# Created By: Tyler Fedrizzi
# Created On: 9 June 2022
#
#
# Description: An implementation of A* in SWARM
# =============================================================================
import math
import numpy as np
import pickle
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import time
import logging

from SWARMRDSClientCore.utilities.algorithm_utils import Algorithm
from SWARMRDSClientCore.utilities.data_classes import Trajectory, MovementCommand, PosVec3
from SWARMRDSClientCore.utilities.log_utils import UserLogger


class AStar(Algorithm):
    """
    A planner that simply passes through the given commands to the
    velocity controller.

    Modified from: https://github.com/AtsushiSakai/PythonRobotics/blob/master/PathPlanning/AStar/a_star.py

    ## Inputs:
    - goal_point [list] Where the agent should head [x,y]
    - map_size [list] The size of the map from the start point to one
                      edge. This value is the offset for the map
    - resolution [float] The resolution of the occupancy map
    - agent_radisu [float] How wide the agent is
    - flight_altitude [float] What altitude the agent should fly at
    """
    def __init__(self,
                 resolution: float,
                 goal_point: list,
                 map_size: list,
                 starting_point: list,
                 agent_radius: float = 0.5,
                 flight_altitude: float = -3.0) -> None:
        super().__init__()
        self.goal_point = PosVec3(X=goal_point[0], Y=goal_point[1], Z=flight_altitude)
        self.resolution = resolution  # Meters
        self.rr = agent_radius  # Meters
        self.map_size = map_size  # Meters (X<Y)
        self.agent_speed = 2.0  # Meters / Second
        # We are in NED Coordinates so -100 is 100 meters behind the starting
        # point
        self.starting_position = starting_point  # Position you start in NED in meters
        self.min_x, self.min_y = -map_size[0], -map_size[1]
        self.max_x, self.max_y = map_size[0], map_size[1]
        self.x_width, self.y_width = map_size[0] * 2, map_size[1] * 2
        self.motion = self.get_motion_model()
        self.flight_altitude = flight_altitude
        self.executing_trajectory = False

    def run(self, **kwargs) -> None:
        """
        Core method that is run every timestemp. Syntax for the module
        is:

        ```
        algo = Astar(goal_point)
        return_args = algo.run()
        ```

        You can extract the appropriate inputs values from Kwargs as
        well, which are determined by what you input in the 
        DefaultSimulationSettings.json file.

        In this example, the map is provided for you by the Mapping
        module and requires no work on your part to extract.
        """
        # Update the map each iteration based upon currently sensed
        # values. Plenty of flexibility here as you could stipulate
        # that one of the inputs be the next goal point that is 
        # determined by another algorithm.
        for key, item in kwargs.items():
            if key == "OccupancyMap":
                self.obstacle_map = item
                break

        if type(self.obstacle_map).__name__ == "NoneType":
            return None

        if not self.executing_trajectory:
            # Plan for the trajectory
            # We start at X=0 and Y=0 in NED coordiantes, but that is map_size[0], map_size[1] in the map
            # We also must make sure that we offset our goal point as well
            self.log.log_message("Requesting a Trajectory from the planner")
            trajectory = self.planning(self.position.X + int(self.map_size[0]) + int(self.starting_position[0]),
                                       self.position.Y + int(self.map_size[1]) + int(self.starting_position[1]),
                                       self.goal_point.X + int(self.map_size[0]) + int(self.starting_position[0]),
                                       self.goal_point.Y + int(self.map_size[1]) + int(self.starting_position[1]))
            self.log.log_message("Trajectory found!")
            self.log.log_message(trajectory.displayPretty())
            self.executing_trajectory = True
            return trajectory
        else:
            time.sleep(0.1)
            # SWARM will ignore these values
            return None

    class Node:
        def __init__(self, x, y, cost, parent_index):
            self.x = x  # index of grid
            self.y = y  # index of grid
            self.cost = cost
            self.parent_index = parent_index

        def __str__(self):
            return str(self.x) + "," + str(self.y) + "," + str(
                self.cost) + "," + str(self.parent_index)

    def planning(self, sx, sy, gx, gy) -> Trajectory:
        """
        A star path search
        input:
            s_x: start x position [m]
            s_y: start y position [m]
            gx: goal x position [m]
            gy: goal y position [m]
        output:
            rx: x position list of the final path
            ry: y position list of the final path
        """

        start_node = self.Node(self.calc_xy_index(sx, self.min_x),
                               self.calc_xy_index(sy, self.min_y), 0.0, -1)
        goal_node = self.Node(self.calc_xy_index(gx, self.min_x),
                              self.calc_xy_index(gy, self.min_y), 0.0, -1)

        open_set, closed_set = dict(), dict()
        print("Grid index is {}".format(self.calc_grid_index(start_node)))
        open_set[self.calc_grid_index(start_node)] = start_node
        iteration = 0
        while True:
            iteration += 1
            if len(open_set) == 0:
                print("Open set is empty..")
                break
            # print(f"Iteration {iteration}")
            c_id = min(
                open_set,
                key=lambda o: open_set[o].cost + self.calc_heuristic(goal_node,
                                                                     open_set[
                                                                         o]))
            current = open_set[c_id]

            if current.x == goal_node.x and current.y == goal_node.y:
                self.log.log_message("Found goal!")
                goal_node.parent_index = current.parent_index
                goal_node.cost = current.cost
                break

            # Remove the item from the open set
            del open_set[c_id]

            # Add it to the closed set
            closed_set[c_id] = current

            # expand_grid search grid based on motion model
            for i, _ in enumerate(self.motion):
                node = self.Node(current.x + self.motion[i][0],
                                 current.y + self.motion[i][1],
                                 current.cost + self.motion[i][2], c_id)
                n_id = self.calc_grid_index(node)
                # If the node is not safe, do nothing
                if not self.verify_node(node):
                    continue

                if n_id in closed_set:
                    continue

                if n_id not in open_set:
                    open_set[n_id] = node  # discovered a new node
                else:
                    if open_set[n_id].cost > node.cost:
                        # This path is the best until now. record it
                        open_set[n_id] = node

        trajectory = self.calc_final_path(goal_node, closed_set)

        return trajectory

    def calc_final_path(self, goal_node, closed_set):
        # generate final course
        trajectory = Trajectory()
        position = PosVec3()
        position.X = self.calc_grid_position(goal_node.x, self.min_x)
        position.Y = self.calc_grid_position(goal_node.y, self.min_y)
        position.Z = self.flight_altitude
        
        command = MovementCommand(position=position, speed=self.agent_speed)
        trajectory.points.append(command)
        parent_index = goal_node.parent_index
        
        traj_point_index = 0
        while parent_index != -1:
            position = PosVec3()
            n = closed_set[parent_index]
            position.X = self.calc_grid_position(n.x, self.min_x)
            position.Y = self.calc_grid_position(n.y, self.min_y)
            position.Z = self.flight_altitude
            command = MovementCommand(position=position, speed=self.agent_speed)
            trajectory.points.append(command)
            traj_point_index += 1
            parent_index = n.parent_index

        # We go from goal to start, so reverse this so we fly start to
        # goal
        trajectory.points.reverse()

        # # Downsample the points by 2
        # new_points = list()
        for i, point in enumerate(trajectory.points):
            if i == 0:
                heading = np.degrees(np.arctan2(point.position.Y - self.position.Y, point.position.X - self.position.X))
            else:
                heading = np.degrees(np.arctan2(point.position.Y - trajectory.points[i - 1].position.Y, point.position.X -  trajectory.points[i - 1].position.X))
            
            trajectory.points[i].heading = heading
            print(heading, trajectory.points[i].heading)

        # trajectory.points = new_points

        return trajectory

    @staticmethod
    def calc_heuristic(n1, n2):
        w = 1.0  # weight of heuristic
        d = w * math.hypot(n1.x - n2.x, n1.y - n2.y)
        return d

    def calc_grid_position(self, index, min_position):
        """
        calc grid position
        :param index:
        :param min_position:
        :return:
        """
        pos = index * self.resolution + min_position + self.map_size[0]
        return pos

    def calc_xy_index(self, position: tuple, min_pos):
        if min_pos > 0:
            return round((position - min_pos) / self.resolution)
        else:
            return round((position + min_pos) / self.resolution)

    def calc_grid_index(self, node: Node):
        return (node.y - self.min_y) * self.y_width + (node.x - self.min_x)

    def verify_node(self, node: Node):
        px = self.calc_grid_position(node.x, self.min_x)
        py = self.calc_grid_position(node.y, self.min_y)
        # print(px, py)
        if px < self.min_x:
            return False
        elif py < self.min_y:
            return False
        elif px >= self.max_x:
            return False
        elif py >= self.max_y:
            return False

        # collision check
        # Numpy is row major so first index is the Y axis and we still need
        # to be sure to offset the points when we check the map
        if self.obstacle_map[node.y + int(self.map_size[1]) + int(self.starting_position[1])][node.x + int(self.map_size[0]) + int(self.starting_position[0])]:
            print("Collided")
            return False

        return True

    @staticmethod
    def get_motion_model():
        # dx, dy, cost
        motion = [[1, 0, 1],
                  [0, 1, 1],
                  [-1, 0, 1],
                  [0, -1, 1],
                  [-1, -1, math.sqrt(2)],
                  [-1, 1, math.sqrt(2)],
                  [1, -1, math.sqrt(2)],
                  [1, 1, math.sqrt(2)]]

        return motion


def plot_trajectory(x_points: list, y_points: list, off_set_x: float, off_set_y: float):
    """
    Plot the calculated trajectory, scaling the points as the saved
    png image is not exactly to scale with the coordinates
    """
    img = plt.imread("maps/occupancy_map.png")
    plt.imshow(img)
    fig = plt.gcf()
    
    for ax in fig.axes:
        # ax.axis('off')
        # ax.margins(0,0)
        # ax.xaxis.set_major_locator(plt.NullLocator())
        # ax.yaxis.set_major_locator(plt.NullLocator())
        # scale = 1.925
        ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(1*(x - off_set_x)/scale))
        ticks_y = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(1*(x - off_set_y)/scale))
        ax.xaxis.set_major_formatter(ticks_x)
        ax.yaxis.set_major_formatter(ticks_y)
    plt.plot(off_set_x,off_set_y, marker='.', color="white", label="Origin")
    plt.plot(x_points, y_points)
    plt.xlabel("X Coordinate (meters)")
    plt.ylabel('Y Coordinate (meters')
    plt.show()

if __name__ == "__main__":
    log = logging.Logger(__name__)
    logger = UserLogger(log, "Drone1")
    planner = AStar([50.0, 30.0], [100.0, 100.0])
    planner.log = logger
    occ_map = None
    # img = plt.imread("maps/occupancy_map.png")
    # plt.imshow(img)
    # plt.show()
    with open("maps/occupancy_map.pickle", "rb") as file:
        occ_map = pickle.load(file)
    # occ_map = occ_map.transpose()
    # occ_map = np.flip(occ_map)
    scale = 2.2
    print(occ_map.shape)
    traj = planner.run(OccupancyMap=occ_map)
    print(traj)
    x_points = list()
    y_points = list()
    for point in traj.points:
        # x_points.append(point.X)
        # y_points.append(point.Y)
        x_points.append(point.X * scale + 175)
        y_points.append(point.Y * scale + 175)
    # plot_trajectory(x_points, y_points, 175.0, 175.0)
