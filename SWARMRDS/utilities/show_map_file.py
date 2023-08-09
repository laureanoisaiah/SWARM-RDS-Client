# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
#
# Created By: Tyler Fedrizzi, Josh Chang
# Created On: 20 January 2023
#
# Description: Load the map files and display the user defined trajectory
# =============================================================================

import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def load_map_metadata(map_name: str) -> None:
    """
    helper function for loading the map metadata
    """
    index = map_name.index("_")
    metadata_name = map_name[:index] + "_metadata" + map_name[index:]
    print(metadata_name)
    with open("../maps/{}.json".format(metadata_name), "r") as file:
        metadata = json.load(file)
    return metadata


def show_map(map_name: str, save_directory: str = "../maps/") -> None:
    """
    Plot and display the trajectories of multiple levels 

    ### Inputs:
    - map_name [str]: Name of the map file
    - save_directory [str]: directory to save the trajectory map (default maps folder)
    """
    
    img = plt.imread("../maps/{}.png".format(map_name))

    map_metadata = load_map_metadata(map_name)
    plt.imshow(img)
    fig = plt.gcf()
    capture_size = map_metadata["CaptureSize"]
    grid_marks = [measure * (1 / map_metadata["CaptureIncrement"]) for measure in capture_size]
    origin_offset = map_metadata["Origin"]
    

    for ax in fig.axes:
        scale = 1e1  # Map is in centimeters
        # Shift the axes of the map by half the bounds of the image, then
        # scale, then reverse both axes to make sense for NED coordinates
        ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(1 * (x - (map_metadata["ImageSize"][0] / 2))/scale))
        ax.xaxis.set_major_formatter(ticks_x)
        ax.yaxis.set_major_formatter(ticks_x)
        
    origin = [grid_marks[0] / 2 + origin_offset[0], grid_marks[1] / 2 + origin_offset[1]]
    plt.plot(origin[0], origin[1], marker='.', color="red", label="1")

    #load the waypoints from the json file
    with open("../tests/DefaultMultiLevelTrajectory.json", "r") as file:
        trajectory = json.load(file)
    level = map_name[(map_name.index("_") + 1):]
    trajectory = trajectory["Trajectories"][level]
    
    
    # Loop through the waypoints and plot the points
    trajectorylist = [origin]
    n = 0
    for waypoint in trajectory:
        plt.plot(origin[0] + (waypoint["X"] * 10), origin[1] + (waypoint["Y"] * 10), marker='.', color="blue", label=n)
        trajectorylist.append([origin[0] + (waypoint["X"] * 10), origin[1] + (waypoint["Y"] * 10)])
        n += 1
    # Loop through the points and draw a line connecting the current point to the next point
    for i in range(len(trajectorylist)-1):
        x = [trajectorylist[i][0], trajectorylist[i + 1][0]]
        y = [trajectorylist[i][1], trajectorylist[i + 1][1]]
        plt.plot(x, y, color="green", linewidth=2)


    plt.xlabel("X Coordinate (meters)")
    plt.ylabel('Y Coordinate (meters)')
    
    # Save the trajectory map to the data assets folder
    #TODO: Define the location of the UE project content folder
    plt.savefig(save_directory + "SWARMHome_{}_Display.png".format(level))
    
    plt.show()


if __name__ == "__main__":
    origin_offset = [[34,34], [36, -57] , [35, 70]]

    # show map for all levels
    for i in range(1, 4):
        show_map("SWARMHome_Home{}".format(i))

