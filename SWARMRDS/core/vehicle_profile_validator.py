# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
#
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: Validator for the Vehicle Profile JSON files that can be
#              used to validate the vehicle profile JSON files
# =============================================================================
import json
import typing

from queue import Queue


class VehicleProfileValidator:
    """
    A Validation system for Vehicle Profiles, which are JSON files that
    define the Phyiscal parameters of a Vehicle that will be simulated
    in the SWARM RDS Physics System.

    ### Arguements:
    - `vehicle_profile_file_name` (str) The name of the vehicle profile
                                        file to validate
    """
    def __init__(self, vehicle_profile_file_name: str, vehicle_type: str, file_path: str, response_queue: Queue = None) -> None:
        self._file_name = vehicle_profile_file_name
        self._file_path = file_path
        self._response_queue = response_queue
        self._vehicle_type = vehicle_type
        self._client_mode = self._response_queue is not None

    def validate(self) -> bool:
        """
        Validate the provided Vehicle Profile JSON file using the
        "ValidPhysicsParameters"
        """
        if self._client_mode:
            self._response_queue.put({"Command": "ValidatePhysicsProfile", "Message": "Validating Vehicle Profile: {}".format(self._file_name)})
        else:
            print("Validating Vehicle Profile: {}".format(self._file_name))
        
        # Load the JSON file
        try:
            with open(self._file_path + "/vehicle_profiles/" + self._file_name, "r") as json_file:
                json_data = json.load(json_file)
        except FileNotFoundError:
            if self._client_mode:
                self._response_queue.put({"Command": "ValidatePhysicsProfile", "Message": "Vehicle Profile with name {} not found!".format(self._file_name)})
            else:
                print("Vehicle Profile not found!")
            return False

        # Load the Valid Physics Parameters

        try:
            with open(self._file_path + "/SWARMRDS/core/SupportedVehiclePhysicsParameter.json", "r") as json_file:
                valid_params = json.load(json_file)
        except FileNotFoundError:
            if self._client_mode:
                self._response_queue.put({"Command": "ValidatePhysicsProfile", "Message": "Valid Physics Parameters file not found in {}/SWARMRDS/core! Please ensure you have at least version 1.4.0 of the Client installed!".format(self._file_path)})
            else:
                print("Valid Physics Parameters not found!")
                print("File path was {}/SWARMRDS/core".format(self._file_path))
            return False
        
        # Retrive the valid parameters for the vehicle type
        valid_params = valid_params[self._vehicle_type]

        # Note that we have different sub-sections that exist. So it is
        # important to check each one individually by the Sub Section
        subsections = valid_params["ValidSubSections"]
        # Check the JSON file for the valid parameters
        for param_name, param_value in json_data["Physics"].items():
            print("DEBUG Parameter Name: {}".format(param_name))
            print("DEBUG Parameter name in subsections: {}".format(param_name in subsections))
            # First, check if the param_name is actually a subsection
            if param_name in subsections:
                for sub_param_name, sub_param_value in param_value.items():
                 
                    # Check the next level down to see if there is another
                    # subsection. Limit this to two levels deep for simplicity
                    if "ValidSubSections" in valid_params[param_name].keys() and sub_param_name in valid_params[param_name]["ValidSubSections"]:
                        # Final level to iterate through
                        for sub_sub_param_name, sub_sub_param_value in sub_param_value.items():
                        
                            # Check the value of the parameter
                            valid, error_msg =  self._check_param_value(sub_sub_param_name, sub_sub_param_value, valid_params, param_name, sub_param_name)

                            if not valid:
                                if self._client_mode:
                                    self._response_queue.put({"Command": "ValidatePhysicsProfile", "Message": error_msg})
                                else:
                                    print(error_msg)
                                return False
                    else:
                        # Check the value of the parameter
                        valid, error_msg =  self._check_param_value(sub_param_name, sub_param_value, valid_params, param_name)

                        if not valid:
                            if self._client_mode:
                                self._response_queue.put({"Command": "ValidatePhysicsProfile", "Message": error_msg})
                            else:
                                print(error_msg)
                            return False
            else:
                # Check the value of the parameter
                valid, error_msg =  self._check_param_value(param_name, param_value, valid_params)

                if not valid:
                    if self._client_mode:
                        self._response_queue.put({"Command": "ValidatePhysicsProfile", "Message": error_msg})
                    else:
                        print(error_msg)
                    return False

        if self._client_mode:
            self._response_queue.put({"Command": "ValidatePhysicsProfile", "Message": "Vehicle Profile Validated Successfully!"})
        else:
            print("Vehicle Profile Validated Successfully!")

        return True           

    def _check_param_value(self, param_name: str, param_value: typing.Any, valid_params: dict, sub_param_name: str = None, sub_sub_param_name: str = None) -> bool:
        """
        Validate the parameter using the param name and access the lower
        values using the sub and sub sub param names as needed.

        ### Inputs:
        - `param_name` (str) The name of the parameter to check
        - `param_value` (Any) The value of the parameter to check
        - `valid_params` (dict) The valid parameters to check against
        - `sub_param_name` (str) The name of the sub parameter to check
        - `sub_sub_param_name` (str) The name of the sub sub parameter to check

        ### Returns:
        - `bool` Whether or not the parameter value is valid
        """
        print("DEBUG Validating parameter with name {} and value {}".format(param_name, param_value))

        # Check the parameter name is actually in the valid parameters
        if sub_param_name is not None:
            if sub_param_name not in valid_params.keys():
                return False, "Sub Parameter name {} is not a valid parameter name!".format(sub_param_name)
            if sub_sub_param_name is not None:
                if sub_sub_param_name not in valid_params[sub_param_name].keys():
                    print(sub_sub_param_name, valid_params[sub_param_name].keys())
                    return False, "Sub Sub Parameter name {} is not a valid parameter name in {}!".format(sub_sub_param_name, sub_param_name)
                if param_name not in valid_params[sub_param_name][sub_sub_param_name].keys():
                    return False, "Parameter name {} is not a valid parameter name!".format(param_name)
                param_info = valid_params[sub_param_name][sub_sub_param_name][param_name]
            else:
                if param_name not in valid_params[sub_param_name].keys():
                    return False, "Parameter name {} is not a valid parameter name!".format(param_name)
                param_info = valid_params[sub_param_name][param_name]
        else:
            if param_name not in valid_params.keys():
                return False, "Parameter name {} is not a valid parameter name!".format(param_name)
            param_info = valid_params[param_name]

        # Check that the type of the parameter is correct
        if type(param_value).__name__ != param_info["Type"]:
            return False, "Parameter {} is not of type {}! Param Type was {}".format(param_name, param_info["Type"], type(param_value).__name__)
        
        # Check that the value is within the valid range if it is a number
        if param_info["Type"] == "float" or param_info["Type"] == "int":
            if param_value < param_info["Min"] or param_value > param_info["Max"]:
                return False, "Parameter {} is not within the valid range of {} to {}!".format(param_name, param_info["Min"], param_info["Max"])
            if "ValidEntries" in param_info.keys():
                if param_value not in param_info["ValidEntries"]:
                    return False, "Parameter {} is not a valid entry in the collection {}!".format(param_name, param_info["ValidEntries"])
        
        # Check that if the value is a string as a part of a collection that
        # it is a valid string in the collection
        if param_info["Type"] == "str":
            if param_info["ValidEntries"] != ["*"] and param_value not in param_info["ValidEntries"]:
                return False, "Parameter {} is not a valid string in the collection {}!".format(param_name, param_info["ValidStrings"])
        
        return True, None


if __name__ == "__main__":
    # Test the validator
    validator = VehicleProfileValidator("SWARMRDS-Multirotor.json", "Multirotor", "../..")
    assert validator.validate()