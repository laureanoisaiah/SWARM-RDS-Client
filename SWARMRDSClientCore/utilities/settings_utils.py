# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
# 
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: Utitilies related to auto-generating files for the SWARM system
# =============================================================================
import os
import json
import traceback


def retrieve_supported_software_modules() -> dict:
    """
    Retrieve the supported software modules contained within the core
    folder.
    """
    with open("{}/../core/SupportedSoftwareModules.json".format(os.getcwd()), "r") as file:
        modules = json.load(file)
    
    return modules["SupportedModules"]

def receive_user_input(input_type: str, 
                       prompt: str,
                       input_range: list = None,
                       isList: bool = False):
    """
    Receive user input and validate the type of input is correct.

    ### Inputs:
    - input_type [str] The type of input we will receive (ie. int)
    - prompt [str] How to prompt the user
    - range [list] A range of values that the input could be.
    """
    if not isList and (input_type == float or input_type == int):
        if input_range == None:
            raise NotImplementedError("You must provide a range for a numeric value!")
    input_receieved = False
    user_input = None
    while not input_receieved:
        try:
            user_input = input(prompt)
            if input_type != str:
                user_input = input_type(user_input)
            if input_type == str and user_input == "":
                print("Error: Input cannot be empty!")
                continue
            if not isinstance(user_input, input_type):
                print("Error: Input type is incorrect! Expected {}. Got {}".format(input_type, type(user_input).__name__))
                continue
            if not isList and (isinstance(user_input, float) or isinstance(user_input, int)):
                if user_input < input_range[0] or user_input > input_range[1]:
                    print("Error! Your input is out of acceptable range. Expected within {}. Got {}".format(input_range, user_input))
                    continue
            if isList and not isinstance(user_input, int):
                print("Error! Please make sure to input an integer choice") 
                continue
            if isList and user_input not in range(1, len(input_range) + 1):
                print("Error! Please choose from the following list of inputs:")
                for i, choice in enumerate(input_range):
                    print("\t{}. {}".format(i + 1, choice))
                continue
            if isList and isinstance(user_input, int):
                user_input = user_input - 1
            input_receieved = True
        except Exception:
            traceback.print_exc()
    
    return user_input


def check_if_have_valid_sensors(module_name: str, sensors: dict) -> bool:
    """
    Check if the user has selected a module but not added the
    appropriate sensors. Example: VideoRecorder but no Camera, which is
    a No Op.

    ### Inputs:
    - module_name [str] The module name selected
    - sensors [dict] The sensor config

    ### Outputs:
    - Whether the current configuration is valid
    """
    if module_name == "VideoRecord" or module_name == "Detector":
        if "Cameras" not in sensors.keys():
            raise AssertionError("You must have a Camera added to this agent to use {}".format(module_name))
    elif module_name == "ObstacleAvoidance":
        if "LiDAR" not in sensors.keys():
            raise AssertionError("You must have a LiDAR added to this agent to use {}".format(module_name))        
    
    return True


def check_if_path_planning_added(modules: dict) -> bool:
    """
    Determine if there is a path planning module added to the user's
    set of software modules.

    ### Inputs:
    - modules [dict] The SoftwareModules loaded for Agent i
    """
    if "LowLevelPathPlanning" not in modules.keys():
        print("Error! You must include a LowLevelPathPlanning module. Please select that now!")
        return False

    return True


def generate_new_user_settings_file(debug: bool = False) -> dict:
    """
    Generate a new Settings file with the provided file name from the
    user.
    """
    print("Generating new settings file!")
    settings = dict(ID=0,
                    SimulationName=None,
                    RunLength=30.0,
                    Scenario=dict(Name=None, Options=dict()),
                    Environment=dict(Name=None,StreamVideo=False),
                    Data=dict(VehicleState=dict(Format="SWARM")),
                    Agents=dict())
    first_prompt = "Please input the name of the simulation you want to run: "
    sim_name = receive_user_input(str, first_prompt)
    if debug:
        print("Simulation Name was {}".format(sim_name))
    print('\n')
    settings["SimulationName"] = sim_name

    second_prompt = "Max time simulation should run in seconds: "
    run_length = receive_user_input(float, second_prompt, [30.0, 9999.0])
    if debug:
        print("Run Length was {}".format(run_length))
    print('\n')
    settings["RunLength"] = run_length

    third_prompt = "What scenario do you want to run:\n"
    options = ["DataCollection"]
    for i, option in enumerate(options):
        third_prompt += "{}. {}\n".format(i + 1, option)
    third_prompt += "Your Choice: "
    scenario_option = receive_user_input(int, third_prompt, options, isList=True)
    if debug:
        print("DEBUG Scenario Option was {}".format(options[scenario_option]))
    print('\n')
    settings["Scenario"]["Name"] = options[scenario_option]

    fourth_prompt = "Would you like to view Simulation Output?:\n"
    options = ["Yes", "No"]
    for i, option in enumerate(options):
        fourth_prompt += "{}. {}\n".format(i + 1, option)
    fourth_prompt += "Your Choice: "
    scenario_option = receive_user_input(int, fourth_prompt, options, isList=True)
    if debug:
        print("DEBUG Stream Video was {}".format(options[scenario_option]))
    bool_options = [option == "Yes" for option in options]
    settings["Environment"]["StreamVideo"] = bool_options[scenario_option]
    if debug:
        print("DEBUG Stream Video is now {}".format(settings["Environment"]["StreamVideo"]))
    print('\n')

    fifth_prompt = "Would you like to collect data?\n"
    options = ["Yes", "No"]
    for i, option in enumerate(options):
        fifth_prompt += "{}. {}\n".format(i + 1, option)
    fifth_prompt += "Your Choice: "
    collect_data = receive_user_input(int, fifth_prompt, options, isList=True)
    print('\n')
    bool_options = [option == "Yes" for option in options]
    if bool_options[collect_data]:
        fifth_prompt_a = "Would you like to collect images?\n"
        fifth_prompt_a_options = ["Yes", "No"]
        for i, option in enumerate(fifth_prompt_a_options):
            fifth_prompt_a += "{}. {}\n".format(i + 1, option)
        fifth_prompt_a += "Your Choice: "
        collect_images = receive_user_input(int, fifth_prompt_a, fifth_prompt_a_options, isList=True)
        bool_options = [option == "Yes" for option in fifth_prompt_a_options]
        if bool_options[collect_images]:
            settings["Data"]["Images"] = dict(Format="PNG")
        print('\n')

        fifth_prompt_b = "Would you like to collect video?\n"
        fifth_prompt_b_options = ["Yes", "No"]
        for i, option in enumerate(fifth_prompt_b_options):
            fifth_prompt_b += "{}. {}\n".format(i + 1, option)
        fifth_prompt_b += "Your Choice: "
        collect_video = receive_user_input(int, fifth_prompt_b, fifth_prompt_b_options, isList=True)
        bool_options = [option == "Yes" for option in fifth_prompt_b_options]
        if bool_options[collect_video]:
            settings["Data"]["Video"] = dict(Format="MP4", VideoName="")
            vid_prompt = "Please input the name of the video to record: "
            video_name = receive_user_input(str, vid_prompt)
            settings["Data"]["Video"]["VideoName"] = video_name
        print('\n')

        fifth_prompt_c = "Would you like to collect vehicle state logs?\n"
        fifth_prompt_c_options = ["Yes", "No"]
        for i, option in enumerate(fifth_prompt_c_options):
            fifth_prompt_c += "{}. {}\n".format(i + 1, option)
        fifth_prompt_c += "Your Choice: "
        collect_state = receive_user_input(int, fifth_prompt_c, fifth_prompt_c_options, isList=True)
        bool_options = [option == "Yes" for option in fifth_prompt_c_options]
        if bool_options[collect_state]:
            settings["Data"]["VehicleState"] = dict(Format="SWARM")
        if debug:
            print("DEBUG {}".format(settings["Data"]))
        print('\n')
    max_numb_agents = 1
    sixth_prompt = "How many agents do you want to create? (Max is {}) ".format(max_numb_agents)
    numb_agents = receive_user_input(int, sixth_prompt, input_range=[1,1])
    for i in range(numb_agents):
        print("Building agent Drone{}\n".format(i))
        agent_settings = dict(Vehicle="Multirotor", AutoPilot="SWARM", Sensors=dict(), Controller=dict(Name="SWARMBase",Gains=dict(P=0.45,I=0.0,D=0.05)), SoftwareModules=dict())
        settings["Agents"]["Drone{}".format(i + 1)] = agent_settings
        
        first_agent_prompt = "What type of Vehicle is this agent?\n"
        first_agent_prompt_options = ["Multirotor"]
        for i, option in enumerate(first_agent_prompt_options):
            first_agent_prompt += "{}. {}\n".format(i + 1, option)
        first_agent_prompt += "Your Choice: "
        vehicle_type = receive_user_input(int, first_agent_prompt, first_agent_prompt_options, isList=True)
        
        if debug:
            print("DEBUG Vehicle Type was {}".format(first_agent_prompt_options[vehicle_type]))
        agent_settings["Vehicle"] = first_agent_prompt_options[scenario_option]
        print('\n')

        second_agent_prompt = "What type of AutoPilot should this agent use?\n"
        second_agent_prompt_options = ["SWARM"]
        for i, option in enumerate(second_agent_prompt_options):
            second_agent_prompt += "{}. {}\n".format(i + 1, option)
        second_agent_prompt += "Your Choice: "
        vehicle_type = receive_user_input(int, second_agent_prompt, second_agent_prompt_options, isList=True)
        
        if debug:
            print("DEBUG Autopilot choice was {}".format(second_agent_prompt_options[vehicle_type]))
        agent_settings["AutoPilot"] = second_agent_prompt_options[scenario_option]
        print('\n')

        agent_third_prompt = "Does this agent have sensors?\n"
        options = ["Yes", "No"]
        for i, option in enumerate(options):
            agent_third_prompt += "{}. {}\n".format(i + 1, option)
        agent_third_prompt += "Your Choice: "
        agent_sensors = receive_user_input(int, agent_third_prompt, options, isList=True)
        bool_options = [option == "Yes" for option in options]
        if bool_options[agent_sensors]:
            agent_third_prompt_a = "\nWould you like to add a Camera (max 1 for now)?\n"
            agent_third_prompt_a_options = ["Yes", "No"]
            for i, option in enumerate(agent_third_prompt_a_options):
                agent_third_prompt_a += "{}. {}\n".format(i + 1, option)
            agent_third_prompt_a += "Your Choice: "
            collect_images = receive_user_input(int, agent_third_prompt_a, agent_third_prompt_a_options, isList=True)
            bool_options = [option == "Yes" for option in agent_third_prompt_a_options]
            if bool_options[collect_images]:
                max_cameras = 1
                if max_cameras > 1:
                    sixth_prompt = "\nHow many cameras do you want to create? (Max is {}) ".format(max_cameras)
                    numb_cameras = receive_user_input(int, sixth_prompt, input_range=[1,1])
                else:
                    numb_cameras = 1
                agent_settings["Sensors"]["Cameras"] = dict()
                for i in range(numb_cameras):
                    
                    print("Setting up Camera{}".format(i))
                    camera_name = "Camera{}".format(i)
                    agent_settings["Sensors"]["Cameras"][camera_name] = dict(X=0.0, Y=0.0, Z=0.0, Settings=dict(Width=640, Height=480))
                    agent_third_prompt_a_1 = "Where is the camera located? (meters in NED coordiantes) "
                    print(agent_third_prompt_a_1)
                    agent_third_prompt_a_2 = "\tX (front of vehicle): "
                    x_cord = receive_user_input(float, agent_third_prompt_a_2, input_range=[-2.0, 2.0])
                    agent_third_prompt_a_3 = "\tY (Right side of vehicle): "
                    y_cord = receive_user_input(float, agent_third_prompt_a_3, input_range=[-2.0, 2.0])
                    agent_third_prompt_a_4 = "\tZ (Height. -Z is up!): "
                    z_cord = receive_user_input(float, agent_third_prompt_a_4, input_range=[-2.0, 2.0])
                    if debug:
                        print("DEBUG Camera located at {},{},{}".format(x_cord, y_cord, z_cord))
                    agent_settings["Sensors"]["Cameras"][camera_name]["X"] = x_cord
                    agent_settings["Sensors"]["Cameras"][camera_name]["Y"] = y_cord
                    agent_settings["Sensors"]["Cameras"][camera_name]["Z"] = z_cord
                    print('\n')
                    agent_third_prompt_a_5 = "What is the camera resolution? (pixels) "
                    print(agent_third_prompt_a_5)
                    agent_third_prompt_a_6 = "\tWidth (640 - 1280) : "
                    width = receive_user_input(int, agent_third_prompt_a_6, input_range=[640, 1280])
                    agent_third_prompt_a_7 = "\tHeight (480 - 720) : "
                    height = receive_user_input(int, agent_third_prompt_a_7, input_range=[480, 720])
                    agent_settings["Sensors"]["Cameras"][camera_name]["Settings"]["Width"] = width
                    agent_settings["Sensors"]["Cameras"][camera_name]["Settings"]["Height"] = height
                    if debug:
                        print("DEBUG Camera Settings are at {}".format(agent_settings["Sensors"]["Cameras"][camera_name]["Settings"]))
            # TODO Add LiDAR options
        print('\n')
        print("Now, we will configure your flight stack!")
        print("Each software module is a piece of code that will run onboard.\n")
        print("================ NOTE ==========================")
        print("You must have a LowLevelPathPlanning module implemented!")
        print("================================================")
        modules_finished = False
        valid_modules = retrieve_supported_software_modules()
        # We iterate through the modules and ask the user to select if they
        # would like to add one or not
        valid_module_names = valid_modules["ValidModuleNames"]
        valid_module_names.append("Finished")
        while not modules_finished:
            eigth_prompt = "Please choose a Module to add (Choose Finished to exit):\n"

            for i, module_name in enumerate(valid_module_names):
                eigth_prompt += "\t{}. {}\n".format(i + 1, module_name)
            eigth_prompt += "Your Choice: "
            module_choice = receive_user_input(int, eigth_prompt, input_range=valid_module_names, isList=True)
            if debug:
                print("DEBUG Module choice was {}".format(valid_module_names[module_choice])) 
            if valid_module_names[module_choice] == "Finished":
                modules_finished = True
                continue
            print("Setting up module {}".format(valid_module_names[module_choice]))
            agent_settings["SoftwareModules"][valid_module_names[module_choice]] = dict(Level=1,States=list(),Parameters=dict(),ClassName=None,)
            class_name_prompt = "Please choose which algorithm you want to use?\n"
            algo_name_options = valid_modules[valid_module_names[module_choice]]["ValidClassNames"]
            for i, algo_option in enumerate(algo_name_options):
                class_name_prompt += "\t{}. {}\n".format(i + 1, algo_option)
            class_name_prompt += "Your Choice: "
            algo_name = receive_user_input(int, class_name_prompt, algo_name_options, isList=True)
            settings["Agents"]["Drone{}".format(i + 1)] = agent_settings
            valid_configuration = check_if_have_valid_sensors(valid_module_names[module_choice], settings["Agents"]["Drone{}".format(i + 1)]["Sensors"])
            if debug:
                print("DEBUG Algorithm name is {}".format(algo_name_options[algo_name]))
            algo_name = algo_name_options[algo_name]
            agent_settings["SoftwareModules"][valid_module_names[module_choice]]["ClassName"] = algo_name
            print("Let's setup the input parameters")
            valid_params = valid_modules[valid_module_names[module_choice]]["ValidParameters"][algo_name]
            for param_name, param in valid_params.items():
                param_prompt = "\tParam Name: {}\n".format(param_name)
                param_prompt += "\tParam Description: {}\n".format(param["description"])
                param_prompt += "\tValid Range: {}\n".format(param["range"])
                param_prompt += "\tEnter a Value: "
                if param["type"] == "int":
                    param_type = int
                    param_setting = receive_user_input(param_type, param_prompt, param["range"])
                elif param["type"] == "float":
                    param_type = float
                    param_setting = receive_user_input(param_type, param_prompt, param["range"])
                elif param["type"] == "str":
                    param_type = str
                    param_setting = receive_user_input(param_type, param_prompt)
                agent_settings["SoftwareModules"][valid_module_names[module_choice]]["Parameters"][param_name] = param_setting

            print("Setting return values automatically!")
            agent_settings["SoftwareModules"][valid_module_names[module_choice]]["ReturnValues"] =  valid_modules[valid_module_names[module_choice]]["ValidReturnValues"][algo_name]
            # Remove that option now that it is setup
            valid_module_names.remove(valid_module_names[module_choice])
            if valid_modules == ["Finished"]:
                settings["Agents"]["Drone{}".format(i + 1)] = agent_settings
                path_planning_added = check_if_path_planning_added(settings["Agents"]["Drone{}".format(i + 1)]["SoftwareModules"])
                if not path_planning_added:
                    continue
                print("All supported modules added! Exiting!")
                modules_finished = True
            settings["Agents"]["Drone{}".format(i + 1)] = agent_settings
        print("Setup for Drone{} completed!".format(i))

    print("===============================")
    print("Setup successfully completed!\n")
    print("===============================")
    if debug:
        print("DEBUG {}".format(settings))
    print("This file will now overwrite the settings/DefaultSimulationSettings.json.")

    overwrite_prompt = "Proceed (Choose No to input a custom file name)?\n"
    options = ["Yes", "No"]
    for i, option in enumerate(options):
        overwrite_prompt += "\t{}. {}\n".format(i + 1, option)
    overwrite_prompt += "Your Choice: "
    overwrite = receive_user_input(int, overwrite_prompt, options, isList=True)
    bool_options = [option == "Yes" for option in options]
    if bool_options[overwrite]:
        with open("../settings/DefaultSimulationSettings.json", "w") as file:
            json.dump(settings, file)
        print("Saved!")
    else:
        name_prompt = "What would you like the name of this file to be (NO .json at the end!)? "
        new_name = receive_user_input(str, name_prompt)
        print("Saving settings file in settings/{}.json".format(new_name))
        with open("../settings/{}.json".format(new_name), "w") as file:
            json.dump(settings, file)
        print("Saved!")

    return settings


if __name__ == "__main__":
    generate_new_user_settings_file(True)