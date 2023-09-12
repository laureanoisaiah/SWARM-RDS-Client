import math

from SWARMRDS.utilities.data_classes import PosVec3


def ned_position_difference(first_pos: PosVec3,
                            second_pos: PosVec3) -> float:
    """
    Calculate the absolute difference in the first position from the
    second position.

    ### Inputs:
    - first_pos [PosVec3] A position in the coordinate frame specified
    - second_pos [PosVec3] A position in the coordinate frame

    ### Return:
    - The difference in position in meters
    """
    return math.sqrt(pow((first_pos.X - second_pos.X), 2)
                     + pow((first_pos.Y - second_pos.Y), 2)
                     + pow((first_pos.Z - second_pos.Z), 2))