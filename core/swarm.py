# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
#
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: Core class for interacting with the SWARM Simulation Framework
# =============================================================================
import json
import traceback
import datetime
import os
import glob
import time
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from uuid import uuid4

from core.client import SWARMClient
from utils.date_utils import convert_datetime_to_str
from utils.settings_utils import receive_user_input, generate_new_user_settings_file


class SWARM():
    """
    Core wrapper that contains all logic for running the SWARM platform.

    ### Arguements:
    - ip_address [str] The API address to connect if you using SWARM in
                       the cloud or remote setting.
    """

    def __init__(self, ip_address: str = "127.0.0.1", debug=False) -> None:
        self.client = SWARMClient(ip_address=ip_address, debug=debug)
        self.ip_address = ip_address
        self.generate_submission_tracking()
        self.map_name = ""
        self.debug = debug

    def regenerate_connection(self) -> None:
        """
        Regenerate the connection since we kill it after the simulation
        is finished.
        """
        self.client = SWARMClient(ip_address=self.ip_address)
        self.client.connect()

    # =========================================================================
    #                       Helper Functions
    # =========================================================================

    def setup_simulation(self,
                         map_name: str = None,
                         settings_file_name: str = "settings/DefaultSimulationSettings.json") -> None:
        """
        Run the setup process for a Simulation, which includes choosing
        what maps to run.

        ### Inputs:
        - map_name [str] The name of the map to load the simulation
        - view_map [bool] Whether you want to view the map
        - settings_file_name [str] The name of the settings file to use
        Default is settings/DefaultSimulationSettings.json

        ### Outputs:
        - None
        """
        input_options = ["Yes", "No"]
        prompt = "Would you like to create a New Settings file?\n(Please input the number for you choice!)\n(Choose No to use settings/DefaultSimulationSettings.json)\n"
        for i, option in enumerate(input_options):
            prompt += "\t{}. {}\n".format(i + 1, option)
        prompt += "Your Choice: "
        user_input = receive_user_input(int, prompt, input_options, isList=True)
        bool_options = [option == "Yes" for option in input_options]
        if bool_options[user_input]:
            new_settings, settings_file_name = generate_new_user_settings_file()

    
        print("Reading map name from {}".format(settings_file_name))
        settings_map_name = self.read_map_name_from_settings(settings_file_name)
        if map_name != settings_map_name:
            self.set_environment_name(settings_file_name, map_name)

        valid = self.validate_environment_name(map_name)

        if not valid:
            print("Environment name is invalid!")
            exit(1)

        input_options = ["Yes", "No"]
        prompt = "Would you like to view a map of the enviroment?\n(Please input the number for you choice!)\n"
        for i, option in enumerate(input_options):
            prompt += "\t{}. {}\n".format(i + 1, option)
        prompt += "Your Choice: "
        user_input = receive_user_input(int, prompt, input_options, isList=True)
        bool_options = [option == "Yes" for option in input_options]
        if bool_options[user_input]:
            # TODO Check if the map file exists and call the appropriate
            # function to get the Map from the Server.
            self.map_name = map_name
            # Run the GUI application to pull up the map
            self.display_map_image_with_coordinates()

    def read_map_name_from_settings(self, settings_file_name: str) -> str:
        """
        Read the map name given from the settings file and validate
        that this is supported before moving on.

        ### Inputs:
        - None

        ### Outputs:
        - A map name as a string
        """
        try:
            with open("{}".format(settings_file_name), "r") as file:
                settings = json.load(file)
            return settings["Environment"]["Name"]
        except Exception:
            traceback.print_exc()
            return ""

    def set_environment_name(self, settings_file_name: str, map_name: str) -> None:
        """
        Set the environment name in the settings file.
        """
        with open("{}".format(settings_file_name), "r") as file:
            settings = json.load(file)
        
        settings["Environment"]["Name"] = map_name

        with open("{}".format(settings_file_name), "w") as file:
            json.dump(settings, file)

        return

    def load_map_metadata(self) -> None:
        """
        Load the metadata for the map to help with the coordinates
        """
        with open("maps/{}_metadata.json".format(self.map_name), "r") as file:
            metadata = json.load(file)
        self.map_metadata = metadata

    def display_map_image_with_coordinates(self) -> None:
        """
        Display the map of the selected environment with the corrected
        coordinate frame. This will show up in MatPlotLib correctly
        so that a user can decide where to send the agent.

        NOTE Map name is "ENVIRONMENT_NAME".png
        TODO Add levels to this as we advance the environment
        """
        img = plt.imread("maps/{}.png".format(self.map_name))
        self.load_map_metadata()
        plt.imshow(img)
        fig = plt.gcf() 
        for ax in fig.axes:
            scale = 1e1  # Map is in centimeters
            # Shift the axes of the map by half the bounds of the image, then
            # scale, then reverse both axes to make sense for NED coordinates
            ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(1 * (x - (self.map_metadata["ImageSize"][0] / 2))/scale))
            ax.xaxis.set_major_formatter(ticks_x)
            ax.yaxis.set_major_formatter(ticks_x)
        plt.xlabel("X Coordinate (meters)")
        plt.ylabel('Y Coordinate (meters)')
        plt.show()

    def generate_submission_tracking(self) -> None:
        """
        Generate the necessary files for submission tracking and 
        history, so that users can track what settings have been 
        changed over time.

        ### Inputs:
        - None

        ### Outputs:
        - None
        """
        print("Checking if submission history exsits")
        os.chdir("settings")
        files = glob.glob("*.json")
        if "SubmissionHistory.json" not in files:
            print("Generating new submission history")
            sub_histroy = {"History": list()}
            with open("SubmissionHistory.json", "a") as file:
                json.dump(sub_histroy, file)
        if "SubmissionList.json" not in files:
            print("Generating new submission list")
            sub_list = {"Submissions": {}}
            with open("SubmissionList.json", "a") as file:
                json.dump(sub_list, file)
        os.chdir("..")
        print("Submission history has been successfully setup!")
        return

    def build_simulation(self,
                         custom_name: str = None,
                         settings_file_name: str = "DefaultSimulationSettings.json",
                         trajectory_file_name: str = "DefaultTrajectory.json",
                         submission_list_location: str = "settings") -> str:
        """
        Build a Simulation Package using the setup from the previous
        step. This creates a new unique name and id to reference all of 
        the simulation steps, including the ability to load this data
        into the SWARM Web Portal for viewing.

        ### Inputs:
        - custom_name [str] A custom name that can be set instead of a 
                            random UUID.

        ### Outputs:
        - The simulation name as a string
        """
        if custom_name:
            sim_name = custom_name
        else:
            sim_name = uuid4()
            sim_name = sim_name.__str__()

        settings, trajectory = self.generate_simulation_package(submission_list_location + "/" + settings_file_name,
                                                                submission_list_location + "/" + trajectory_file_name,
                                                                sim_name)

        with open("{}/SubmissionList.json".format(submission_list_location), "r") as file:
            submission_list = json.load(file)

        print(submission_list["Submissions"].keys())
        print("Building submission package for {}".format(sim_name))
        if sim_name in submission_list["Submissions"].keys():
            submission_list["Submissions"][sim_name]["Settings"] = settings
            submission_list["Submissions"][sim_name]["Trajectory"] = trajectory
            submission_list["Submissions"][sim_name]["Number Of Runs"] += 1
        else:
            submission_list["Submissions"][sim_name] = {
                "Completed": False,
                "Settings": settings,
                "Trajectory": trajectory,
                "Created": convert_datetime_to_str(datetime.datetime.now()),
                "Submitted": True,
                "Number Of Runs": 1
            }

        with open("{}/SubmissionList.json".format(submission_list_location), "w") as file:
            json.dump(submission_list, file)

        return sim_name

    def generate_simulation_package(self,
                                    settings_file_name: str,
                                    trajectory_file_name: str,
                                    sim_name: str) -> tuple:
        settings = self.read_json_file(settings_file_name)
        settings = self.add_simulation_name_to_settings(sim_name, settings, settings_file_name)
        trajectory = self.read_json_file(trajectory_file_name)
        return settings, trajectory

    def add_simulation_name_to_settings(self,
                                        sim_name: str,
                                        settings: str,
                                        settings_file_name: str) -> str:
        """
        Update the name of the simulation name in the settings file.
        """
        settings = json.loads(settings)
        settings["SimulationName"] = sim_name
        print(settings)
        print(settings_file_name)
        with open("{}".format(settings_file_name), "w") as file:
            json.dump(settings, file)
        settings = json.dumps(settings)
        return settings

    def read_json_file(self, file_name: str) -> str:
        """
        Read a JSON file and then return the string form of the file so
        that we can send this to the server.

        ### Inputs:
        - file_name [str] The file to read from

        ### Outputs:
        - The contents of the JSON file as a JSON string
        """
        with open(file_name, "r", encoding="utf-8") as file:
            code = json.load(file)

        return json.dumps(code)

    def retrieve_sim_package(self, sim_name: str, folder: str = "settings") -> tuple:
        """
        Retrieve the settings files as JSON strings to send to the
        server.

        ### Inputs:
        - sim_name [str] The unique simulation name

        ### Outputs:
        - The settings, trajectory and vehicle settings to send to the
          server
        """
        with open("{}/SubmissionList.json".format(folder), "r") as file:
            submission_list = json.load(file)

        try:
            settings = submission_list["Submissions"][sim_name]["Settings"]
            trajectory = submission_list["Submissions"][sim_name]["Trajectory"]
        except KeyError:
            print("{} doesn't exist in the submission list! Please try a different name!".format(
                sim_name))

        return settings, trajectory

    def update_submission_list(self, message: dict, folder: str = "settings") -> None:
        """
        Once we have received a finish message, update the submission
        list to reflect this fact.

        ### Inputs:
        - message [dict] - The message received from the client

        Message should have the following format:
        {
            "Sim_name": self.settings["SimulationName"],
            "Status": "NotCompleted",
            "Minutes": 5
            "Seconds": 12
        }

        ### Outputs:
        - None
        """
        with open("{}/SubmissionList.json".format(folder), "r") as file:
            sub_list = json.load(file)
        
        with open("{}/SubmissionHistory.json".format(folder), "r") as file:
            history = json.load(file)

        try:
            submission = sub_list["Submissions"][message["Sim_name"]]
            if message["Status"] == "Completed":
                submission["Completed"] = True
                print("Simulation {} has been completed!".format(message["Sim_name"]))
                print("Completion Time: {} Mins {} Seconds".format(message["Minutes"], message["Seconds"]))
            history["History"].append(submission)
            with open("{}/SubmissionList.json".format(folder), "w") as file:
                json.dump(sub_list, file)
            with open("{}/SubmissionHistory.json".format(folder), "w") as file:
                json.dump(history, file)
        except KeyError:
            traceback.print_exc()
            print("This simulation was not apart of the Submission List")
        except Exception:
            traceback.print_exc()

    def access_environment_list(self) -> list:
        """
        Retrieve the environment list to determine what environments
        are supported.
        """
        try:
            files = os.listdir("settings")
            assert "SupportedEnvironments.json" in files
            with open("settings/SupportedEnvironments.json", "r") as file:
                envs = json.load(file)
            return envs["Environments"]
        except AssertionError:
            print("The file settings/SupportedEnvironments.json does not exist!")
            return False
        except Exception:
            traceback.print_exc()
            return False

    # =========================================================================
    #                       Validation Functions
    # =========================================================================

    def validate_environment_name(self, map_name: str, folder: str = "settings") -> bool:
        """
        Given a User-defined string, validate that the string contains
        a supported map name of an environment the SWARM Core system
        actually supports.

        ### Inputs:
        - map_name [str] The map name to run

        ### Outputs:
        - A boolean describing whether the map name is valid
        """
        try:
            assert isinstance(map_name, str)
            with open("{}/SupportedEnvironments.json".format(folder), "r") as file:
                envs = json.load(file)
        
            if map_name in envs["Environments"]:
                return True
            else:
                return False
        except AssertionError:
            print("The provided map name is not a string!")
            return False
        except Exception:
            traceback.print_exc()
            return False

    def validate_scenario_name(self, scenario_name: str, folder: str = "settings") -> bool:
        try:
            assert isinstance(scenario_name, str)
            with open("{}/SupportedScenarios.json".format(folder), "r") as file:
                scenarios = json.load(file)
            if scenario_name in scenarios["Scenarios"]:
                return True
            else:
                print("Error! {} is not a supported scenario".format(scenario_name))
                return False
        except AssertionError:
            print("The provided scenario name is not a string!")
            return False
        except Exception:
            traceback.print_exc()
            return False

    def validate_settings_file(self, settings_file: dict) -> bool:
        """
        Validate the settings file provided by the user before sending
        this to the SWARM Core Server. Provide information about
        acceptable values for each parameter field.

        ### Inputs:
        - settings_file [dict] The JSON file as a dictionary containing
                               the settings for the SWARM Core system
        
        ### Outputs:
        - A boolean indicating whether the file is valid or not
        """
        key_components = ["ID", "RunLength", "SimulationName", "Scenario", "Environment", "Agents"]
        if "Data" in settings_file.keys():
            key_components.append("Data")
        try:
            # First, validate that all required sections are present
            try:
                assert list(settings_file.keys()).sort() == key_components.sort()
            except AssertionError:
                print("The required components are not containined in this file.")
                print("Required Components: {}".format(key_components))
                print("What you submitted: {}".format(list(settings_file.keys())))
                return False

            # Next, validate each section
            for key, options in settings_file.items():
                if key == "ID":
                    try:
                        assert isinstance(options, int)
                    except AssertionError:
                        print("The required ID is not an integer. Please regenerate this file.")
                        return False
                elif key == "RunLength":
                    try:
                        assert (isinstance(options, int) or isinstance(options, float))
                        if not (options >= 30.0 and options <= 9999):
                            raise ValueError()
                    except AssertionError:
                        print("The required Run Length is not an integer or float. Please fix this!")
                        return False
                    except ValueError:
                        print("The Run Length specified is not a valid value.")
                        print("Valid values are 30.0 to 9999.0 seconds")
                        print("Please change this value in your settings file")
                        return False
                elif key == "Scenario":
                    valid_keys = ["Name", "Options"]
                    try:
                        if valid_keys != list(options.keys()):
                            raise AssertionError("Error! Please ensure you have the following sections: {}".format(valid_keys))
                        if not self.validate_scenario_name(options["Name"]):
                            raise AssertionError("Scenario with name {} is not supported!".format(options["Name"]))
                        if "LevelNames" in options["Options"]:
                            for level_name in options["Options"]["LevelNames"]:
                                if not self.validate_level_is_supported(settings_file["Environment"]["Name"], level_name):
                                    raise AssertionError("Level {} is not supported for environment with name {}!".format(level_name, settings_file["Environment"]["Name"]))
                        if "MultiLevel" in options["Options"]:
                            if not isinstance(options["Options"]["MultiLevel"], bool):
                                raise AssertionError("Error! The field MultiLevel must be a boolean value!")
                    except AssertionError as error:
                        print(error)
                        return False
                elif key == "Environment":
                    valid_keys = ['Name', 'StreamVideo', 'StartingLevelName']
                    try:
                        if not "Name" in list(options.keys()):
                            raise AssertionError('You must provide a Name that is in the environment')
                        if not self.validate_environment_name(options["Name"]):
                            raise AssertionError("Environment name {} is not valid!".format(options["Name"]))
                        if not isinstance(options["StreamVideo"], bool):
                            raise AssertionError("Error! Please ensure the StreamVideo section is a boolean value")
                        if not isinstance(options["StartingLevelName"], str):
                            raise AssertionError("Error! Please ensure the Level name is a string value")
                        if options['StartingLevelName'] not in settings_file["Scenario"]["Options"]["LevelNames"]:
                            raise AssertionError('Error! You must choose a level name that is in the Scenario Levels selected!\nValid options are: {}'.format(settings_file["Scenario"]["Options"]["LevelNames"]))
                        if not self.validate_level_is_supported(options["Name"], options['StartingLevelName']):
                            raise AssertionError("Level selected is not supported by this environment")
                    except AssertionError as error:
                        print(error)
                        return False
                elif key == "Data":
                    valid_options = ["Images", "VehicleState", "Video"]
                    valid_image_types = ["PNG"]
                    valid_video_types = ["MP4"]
                    try:
                        for type in options.keys():
                            if not type in valid_options:
                                raise AssertionError("Error! {} is not a valid type of data to collect".format(type))
                            if type == "Images":
                                if not options["Images"]["Format"] in valid_image_types:
                                    raise AssertionError("Error! {} is not a valid image format to save collected images".format(type))
                            elif type == "Video":
                                if not options["Video"]["Format"] in valid_video_types:
                                    raise AssertionError("Error! {} is not a valid video form to save collected collected".format(type))
                    except AssertionError as error:
                        print(error)
                        return False
                elif key == "Agents":
                    # Test that they have an agent
                    try:
                        numb_agents = len(list(options.keys()))
                        if numb_agents < 1 or numb_agents > 1:
                            raise AssertionError("Error! Only 1 agent is supported at the moment! Please contact Codex Labs to request multi-agent support!")
                    except Exception as error:
                        print(error)
                        # This is a critical error that should not allow them to continue
                        return False
                    # Now, iterate through each agent and check that the modules are there
                    for agent, agent_options in options.items():
                        print("Validating {}".format(agent))
                        # Test that the appropriate sections exist
                        valid_agent_sections = ["Vehicle", "AutoPilot", "Sensors", "Controller", "SoftwareModules"]
                        valid_agent_sections.sort()
                        try:
                            user_agent_options = list(agent_options.keys())
                            user_agent_options.sort()
                            if not user_agent_options == valid_agent_sections:
                                raise AssertionError("Sections for {} are not valid!\nYour Options: {}\nValid Options: {}".format(agent, user_agent_options, valid_agent_sections))
                        except Exception as error:
                            traceback.print_exc()
                            return False
                        for section_name, section in agent_options.items():
                            if section_name == "Vehicle":
                                if not section == "Multirotor":
                                    raise AssertionError("Vehicle parameter must be Multirotor. Support for different vehicle types coming soon!")
                            elif section_name == "AutoPilot":
                                if not section == "SWARM":
                                    raise AssertionError("Autopilot parameter must be SWARM. Support for different autopilots, including PX4/Ardupilot coming in February 2023!")
                            elif section_name == "Sensors":
                                valid_sensor_types = ["Cameras", "LiDARs"]
                                for sensor_type, sensor_settings in section.items():
                                    if sensor_type not in valid_sensor_types:
                                        raise AssertionError("{} is not a supported sensor in SWARM. Please contact Codex Labs to request support for this sensor!".format(sensor_type))
                                    if sensor_type == "Cameras":
                                        for camera_name, camera_options in sensor_settings.items():
                                            print("Validating camera {}".format(camera_name))
                                            if len(section["Cameras"].keys()) < 1:
                                                raise AssertionError("You must have at least 1 camera in this section!")
                                            valid_camera_sections = ["X", "Y", "Z", "Settings"]
                                            valid_camera_sections.sort()
                                            sensor_settings_sections = list(camera_options.keys())
                                            sensor_settings_sections.sort()
                                            if sensor_settings_sections != valid_camera_sections:
                                                raise AssertionError("{} has invalid settings.\nYour Sections: {}\nRequired Sections: {}".format(camera_name, sensor_settings_sections, valid_camera_sections))
                                            for sensor_setting_key, sensor_setting in camera_options.items():
                                                if sensor_setting_key == "X" or sensor_setting_key == "Y" or sensor_setting_key == "Z":
                                                    # TODO We need to define these bounds somewhere relative to the environment
                                                    if not isinstance(sensor_setting, float) or (sensor_setting < -50.0 or sensor_setting > 50.0):
                                                        raise AssertionError("{} for {} is not a float value within -50.0 and 50.0".format(sensor_setting_key, agent))
                                                elif sensor_setting_key == "Settings":
                                                    valid_camera_setting_sections = ["Width", "Height"]
                                                    user_camera_setting_sections = list(sensor_setting.keys())
                                                    if (user_camera_setting_sections != valid_camera_setting_sections):
                                                        raise AssertionError("Camera {} for agent {} settings are invalid.\nYour sensor settings section: {}\nValid sensor setting section: {}".format(camera_name, agent, user_camera_setting_sections, valid_camera_setting_sections))
                                                    for camera_setting_key, camera_setting in sensor_setting.items():
                                                        if camera_setting_key == "Width":
                                                            if float(camera_setting) > 1280.0 or float(camera_setting) < 640.0:
                                                                raise AssertionError("Camera {} for agent {} width parameter must be between 640 and 1280!\nYour input: {}".format(camera_name, agent, camera_setting))
                                                            elif camera_setting_key == "Height":
                                                                if float(camera_setting) > 720.0 or float(camera_setting) < 480.0:
                                                                    raise AssertionError("Camera {} for agent {} width parameter must be between 640 and 1280!\nYour input: {}".format(camera_name, agent, camera_setting))
                            elif section_name == "Controller":
                                valid_controller_sections = ["Name", "Gains"]
                                for controller_section_name, controller_setting in section.items():
                                    if controller_section_name not in valid_controller_sections:
                                        raise AssertionError("Controller for {} has an invalid field!\nYour input: {}\nValid Inputs: {}".format(agent, controller_section_name, valid_controller_sections))
                                    if controller_section_name == "Name":
                                        if not controller_setting == "SWARMBase":
                                            raise AssertionError("Controller for {} type is is invalid. Name must be SWARMBase. Support for different controllers will be available in March 2023!".format(agent))
                                    elif controller_section_name == "Gains":
                                        for gain_key, gain in controller_setting.items():
                                            if not isinstance(gain, float):
                                                raise AssertionError("Gain {} for controller for {} must be a float value!".format(gain_key, agent))
                                            if gain < 0.0 or gain > 20.0:
                                                raise AssertionError("Gain {} for controller for {} must be between 0.0 and 20.0!".format(gain_key, agent))
                            elif section_name == "SoftwareModules":
                                self.validate_software_modules(section, agent)
                print("Section {} is valid!".format(key))    
            return True
        except Exception:
            traceback.print_exc()
            return False

    def validate_software_modules(self, modules: dict, agent_name: str) -> bool:
        """
        Validate the individual software modules for a specific agent.
        Ensure that each selected parameter is valid and that the
        version of SWARM the user has is valid as well!

        Any assertion we make gets caught by the try, except in the
        main function that calls this.
        """
        with open("core/SupportedSoftwareModules.json", "r") as file:
            supported_modules = json.load(file)
        supported_modules = supported_modules["SupportedModules"]
        for module_name, settings in modules.items():
            if module_name not in supported_modules.keys():
                raise AssertionError("{} module for agent {} is not supported!\nValid modules are {}".format(module_name, agent_name, supported_modules.keys()))
            valid_class_names = supported_modules[module_name]["ValidClassNames"]
            class_name = settings["ClassName"]
            if class_name not in valid_class_names:
                raise AssertionError("Class name {} for {} is invalid.\nValid options are {}".format(class_name, module_name, valid_class_names))
            for setting_name, setting in settings.items():
                if setting_name not in supported_modules["ValidModuleParameters"]:
                    raise AssertionError("Invalid module paramter in {}!\n Valid options are {}.".format(module_name, supported_modules["ValidModuleParameters"]))
                if setting_name == "Level":
                    if not isinstance(setting, int) or not (setting in [1,2,3]):
                        raise AssertionError("Level parameter for {} is invalid.\nValid options are {}".format(module_name, [1,2,3]))
                elif setting_name == "States":
                    pass
                elif setting_name == "Parameters":
                    valid_params = supported_modules[module_name]["ValidParameters"][class_name]
                    for param_name, value in setting.items():
                        if not param_name in valid_params.keys():
                            raise AssertionError("Parameter {} for {} is invalid.\nValid options are {}\nYour Input: {}".format(param_name, module_name,valid_params[param_name], value))
                        if not type(value).__name__ == valid_params[param_name]["type"]:
                            raise AssertionError("Parameter {} for {} is an invalid type.\nValid options are {}\nYour Input: {}".format(param_name, module_name, valid_params[param_name]["type"], type(value).__name__))
                        if (value  < valid_params[param_name]["range"][0] or value > valid_params[param_name]["range"][1]):
                            raise AssertionError("Parameter {} for {} is not in a valid range.\nValid options are {}\nYour Input: {}".format(param_name, module_name, valid_params[param_name]["range"], value))
                elif setting_name == "InputArgs":
                    valid_args = supported_modules[module_name]["ValidInputArgs"][class_name]
                    for param_name, value in setting.items():
                        if not param_name in valid_args.keys():
                            raise AssertionError("Input Arg {} for {} is invalid.\nValid options are {}".format(param_name, module_name,valid_args))
                        if not type(value).__name__ == valid_args[param_name]["type"]:
                            raise AssertionError("Input Arg {} for {} is an invalid type.\nValid options are {}".format(param_name, module_name, valid_args[param_name]["type"]))
                        if not value in valid_args[param_name]["range"]:
                            raise AssertionError("Input Arg {} for {} is not in a valid range.\nValid options are {}".format(param_name, module_name, valid_args[param_name]["range"]))
                elif setting_name == "ReturnValues":
                    valid_return_values = supported_modules[module_name]["ValidReturnValues"][class_name]
                    for return_value in setting:
                        if not return_value in valid_return_values:
                            raise AssertionError("Return Value {} for {} is invalid.\nValid options are {}\nYour Input: {}".format(return_value, module_name, valid_return_values, value))

        return True

    def validate_multi_level_trajectory_file(self, trajectory: dict) -> bool:
        """
        Iteration through multi-level trajectory files. 

        ### Inputs:
        - trajectory [dict] - list of trajectories

        ### Outputs:
        - trajectory_valid [bool] - True if the trajectory is valid, False otherwise
        """
        # We always want to keep the trajectory definition the same, as this
        # will confuse the user if they have to put different names  for what
        # is basically the same system.

        # Always access the Trajectory via Trajectory, especially for Core
        trajectory = trajectory["Trajectory"]
        if isinstance(trajectory, list):
            trajectory_valid = self.validate_trajectory_file(trajectory)
        else:
            # trajectory = trajectory["Trajectories"]
            for level in trajectory.keys():
                trajectory_valid = self.validate_trajectory_file(trajectory[level])
                
        return trajectory_valid

    def validate_trajectory_file(self, trajectory: dict) -> bool:
        """
        Validate the given trajectory file is valid to be run on the
        SWARM Simulation Platform.

        ### Inputs:
        - trajectory [dict] The trajectory to follow, given as a list
                            of points in the NED coordinate frame with

        ### Outputs:
        - A boolean value saying whether the trajectory is valid or not          
        """
        try:
            print("Validating the Trajectory!")
            # trajectory = trajectory[next(iter(trajectory))]
            if len(trajectory) == 0:
                raise AssertionError("Error! Your trajectory must contain at least 1 point!")
            valid_point_fields = ["X", "Y", "Z", "Heading", "Speed"]
            for i, point in enumerate(trajectory):
                print("Validing point {} of {} of the trajectory!".format(i, len(trajectory)))
                if not isinstance(point, dict):
                    raise AssertionError("Error! The point definition must be a dictionary!\nYour Input: {}".format(type(point).__name__))
                for field_name, value in point.items():
                    if not isinstance(value, float):
                        raise AssertionError("Type {} for field name {} is an invalid type! You must input a float value!".format(type(value).__name__, field_name))
                    if field_name not in valid_point_fields:
                        raise AssertionError("The provided field name for the point is invalid!")
                    if field_name == "X" or field_name == "Y":
                        if value > 1000.0 or value < -1000.0:
                            raise AssertionError("{} value is invalid. Valid range is [-1000.0, 1000.0].".format(field_name))
                    elif field_name == "Z":
                        if value > 0.5:
                            print("WARNING! You have input a Z value that is greater the 0.5, which is below the starting point of the agent (ie. in the ground). Giving these values should only be done if you know the agent will not hit the ground and a negative value should be given for 'positive' altitude. ")
                        if value > 1000.0 or value < -1000.0:
                            raise AssertionError("{} value is invalid. Valid range is [-1000.0, 1000.0].".format(field_name))
                    elif field_name == "Heading":
                        if value  < -360.0 or value > 360.0:
                            print("WARNING! You input a heading value greater then 360 or less than -360. This will be truncated to a proper value!")
                    elif field_name == "Speed":
                        if value < 0.0 or value > 20.0:
                            raise AssertionError("Speed value is invalid! Valid range is 0.0 to 20.0 meters per second!")
            return True
        except AssertionError as error:
            print(error)
            return False
        except Exception:
            traceback.print_exc()
            return False


    def validate_level_is_supported(self, env_name: str, level_name: str) -> bool:
        """
        Validate that the level selected in the environment is valid.
        We always validate the environment name before we validate
        the level name, so we can say envs[env_name]["Levels"] easily
        enough.

        ### Inputs:
        - env_name [str] The name of the environment to run
        - level_name [str] The name of the level inside of the environment to run

        ### Outputs:
        - A boolean determining if this level is supported or not
        """
        with open("settings/SupportedEnvironments.json") as file:
            envs = json.load(file)
        try:
            levels = envs['Environments'][env_name]['Levels']
            assert level_name in levels
            return True
        except AssertionError:
            print("Error! Level {} does not exist!\nSupported Levels are: {}".format(level_name, levels))
        except Exception:
            traceback.print_exc()
            return False

    # =========================================================================
    #                       Core Message Functions
    # =========================================================================
    def run_simulation(self,
                       map_name: str,
                       sim_name: str,
                       folder: str = "settings") -> bool:
        """
        Run a Simulation, waiting for the server to tell us when it has
        been completed.

        TODO This should be an Async function that allows the user
        to do other things.

        ### Inputs:
        - map_name [str] The map to run
        - sim_name [str] The name of the sim to run

        ### Outputs:
        - Returns an indicator of whether the simulation has been 
          completed
        """
        try:
            # Only connect once we are ready to send a command
            
            print("Running simulation {}".format(sim_name))

            settings, trajectory = self.retrieve_sim_package(
                sim_name, folder=folder)
            settings_valid = self.validate_settings_file(json.loads(settings))
            trajectory_valid = self.validate_multi_level_trajectory_file(json.loads(trajectory))
            if not settings_valid:
                print("Simulation Run Failed.\nReason: Settings file invalid! Please see the settings folder!")
                exit(1)
            if not trajectory_valid:
                print("Simulation Run Failed.\nReason: Trajectory file invalid! Please see the settings folder!")
                exit(1)
            self.client.connect()
            message = {
                "Command": "Run Simulation",
                "Settings": settings,
                "Trajectory": trajectory,
                "Sim_name": sim_name,
                "Map_name": map_name
            }
            completed = self.client.send_simulation_execution_package(
                message)
            if "Error" in completed.keys():
                print("There was an error!")
                print(completed["Error"])
                return False
            else:
                self.update_submission_list(completed, folder=folder)
                assert completed["Status"] == "Completed"
                return completed["Status"] == "Completed"
        except AssertionError:
            print("Simulation could not be completed!")
            return False
        except Exception:
            traceback.print_exc()
            exit(1)

    def run_view_only_simulation(self,
                       map_name: str,
                       sim_name: str,
                       folder: str = "settings") -> bool:
        """
        Run a Simulation, waiting for the server to tell us when it has
        been completed.

        TODO This should be an Async function that allows the user
        to do other things.

        ### Inputs:
        - map_name [str] The map to run
        - sim_name [str] The name of the sim to run

        ### Outputs:
        - Returns an indicator of whether the simulation has been 
          completed
        """
        try:
            # Only connect once we are ready to send a command
            
            print("Running simulation {}".format(sim_name))

            settings, trajectory = self.retrieve_sim_package(
                sim_name, folder=folder)
            settings_valid = self.validate_settings_file(json.loads(settings))
            if not settings_valid:
                print("Simulation Run Failed.\nReason: Settings file invalid! Please see the settings folder!")
                exit(1)

            self.client.connect()
            message = {
                "Command": "View Level",
                "Settings": settings,
                "Trajectory": trajectory,
                "Sim_name": sim_name,
                "Map_name": map_name
            }
            completed = self.client.send_simulation_execution_package(
                message)
            if "Error" in completed.keys():
                print("There was an error!")
                print(completed["Error"])
                return False
            else:
                self.update_submission_list(completed, folder=folder)
                assert completed["Status"] == "Completed"
                return completed["Status"] == "Completed"
        except AssertionError:
            print("Simulation could not be completed!")
            return False
        except Exception:
            traceback.print_exc()
            exit(1)

    def extract_data(self,
                     sim_name: str) -> bool:
        """
        Run a Simulation, waiting for the server to tell us when it has
        been completed. Ensure that we send an access key to validate
        that we can get access to the system.

        TODO This should be an Async function that allows the user
        to do other things.

        ### Inputs:
        - sim_name [str] The name of the sim to run

        ### Outputs:
        - Returns an indicator of whether the extraction has been 
          completed
        """
        try:
            print("Running Data Extraction for Simulation {}".format(sim_name))
            
            time.sleep(1)
            # TODO Add regenerate logic
            if not self.client.connected:
                self.regenerate_connection()

            message = {
                "Command": "Extract Data",
                "SimName": sim_name
            }
            if self.debug:
                print(f"DEBUG: Sending {message}")
            completed = self.client.send_data_extraction_message(
                message)
            if isinstance(completed, bool):
                return completed
            if "Error" in completed.keys():
                print("There was an error!")
                print(completed["Error"])
                return False
            else:
                return True
        except AssertionError:
            print("Simulation could not be completed!")
            return False
        except KeyboardInterrupt:
            print("Shutting down connection!")
            self.client.close()
        except Exception:
            traceback.print_exc()

    def retreive_supported_environments(self) -> bool:
        """
        Retrieve the supported environments from the SWARM Core
        and provide those as a JSON file stored in the `settings` folder
        called `SupportedEnvironments.json`.

        ### Inputs:
        - None

        ### Outputs:
        - None
        """
        try:
            print("Requesting the supported environemtns from SWARM Core")
            
            time.sleep(1)
            # TODO Add regenerate logic
            if not self.client.connected:
                self.regenerate_connection()

            message = {
                "Command": "Supported Environments",
            }
            # Returns the body of the message containing the list
            # of supported environments
            environments = self.client.send_supported_envs_message(
                message)
            if isinstance(environments, bool):
                return environments
            elif "Error" in environments.keys():
                print("There was an error!")
                print(environments["Error"])
                return False
            else:
                print("Supported Environments with SWARM Container:")
                for env_name in environments["SupportedEnvironments"]:
                    print("\t{}".format(env_name))
    
                with open("settings/SupportedEnvironments.json", "w") as file:
                    json.dump({"Environments": environments["SupportedEnvironments"]}, file)
                return True
        except AssertionError:
            print("Simulation could not be completed!")
            return False
        except Exception:
            traceback.print_exc()

    def retreive_environment_information(self, env_name: str) -> bool:
        """
        Retrieve the map and metadata from the SWARM Core
        instance. This will reach out to the server and download
        a map_data.tar.gz file containing the map information of the
        environment provided.

        ### Usage:
        - Create a sim manager with
          `sim_manager = SWARM()`
        - Call this method and wait to receive the required files

        ### Inputs:
        - env_name [str] The name of the environment

        ### Outputs:
        - A boolean telling you whether this worked or not
        """
        try:
            print("Requesting the map information for {} environment from SWARM Core".format(env_name))
            
            time.sleep(1)
            # TODO Add regenerate logic
            if not self.client.connected:
                self.regenerate_connection()

            message = {
                "Command": "Environment Information",
                "EnvironmentName": env_name
            }
            if self.debug:
                print(f"DEBUG: Sending {message}")
            completed = self.client.send_env_information_message(
                message)
            if self.debug:
                print(f"DEBUG: Received {completed}")
            if isinstance(completed, bool):
                return completed
            if "Error" in completed.keys():
                print("There was an error!")
                print(completed["Error"])
                return False
            else:
                return True
        except AssertionError:
            print("Simulation could not be completed!")
            return False
        except Exception:
            traceback.print_exc()