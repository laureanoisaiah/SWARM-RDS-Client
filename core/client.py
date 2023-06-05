# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
#
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: Core Execution of the forward-facing gui
# =============================================================================
import socket
import json
import time
import traceback
import os
import machineid
import subprocess
import sys

from tqdm import tqdm
from threading import Thread, Event
from json import JSONDecodeError

from core.validator import activate_license

# from utils.constants import ENCODING_SCHEME
ENCODING_SCHEME = "utf-8"
BUFFER_SIZE = 4096 * 2
MAX_PACKET_SIZE = 2048 * 2


class SWARMClient(Thread):
    """
    Core client class that handles interfacing with the SWARM API for
    running and managing simulations.

    ## Arguments:
    - port [int] The port on the machine to talk to
    - ip_address [str] the ip address to communicate with
    - debug [bool] A flag for debugging
    """

    def __init__(self, ip_address: str = "127.0.0.1", port: int = 5002, debug: bool = False) -> None:
        super().__init__(daemon=True)
        self.address = ip_address
        self.port = port
        # TODO Find a way to make this a isolated variable
        self.connected = False
        self.message_map = dict()
        self.message_id = 0
        self.shutdown_requested = Event()
        self.debug = debug
        self.license_key = ""
        self.license_activated = False
        self.encoding = "utf-8"
        # Save the last response provided
        self.last_response = dict()
        self.machine_id = machineid.hashed_id('swarm-dev')
        self.load_license_key()
        self.activate_user_license()

    def start(self) -> None:
        """
        Overwrites the standard thread message for starting a client.

        ### Inputs:
        - None

        ### Outputs:
        - None
        """
        print("Starting SWARM Client")
        super().start()

    def load_license_key(self) -> None:
        """
        Load the license key from the settings file. Stop program
        execution if this file doesn't exist.
        """
        try:
            with open("settings/LicenseKey.json", "r") as file:
                license_key = json.load(file)
            self.license_key = license_key["Key"]
            self.license_activated = license_key["Activated"]
            self.account_id = license_key["AccountID"]
        except FileNotFoundError:
            raise AssertionError("Error! License file with name LicenseKey.json not found!")
        except KeyError:
            raise AssertionError("Error! No field named 'Key' was found in the license file.\nPlease use the following format:\n\n{\n'Key': LICENSE_KEY,\n'Activate': false\n}")
        except Exception:
            traceback.print_exc()
            exit(1)

    def activate_user_license(self) -> bool:
        """
        Activate the user license by correlating this machine with
        this user id.

        ### Inputs:
        - None

        ### Outputs:
        - Boolean of whether the activation was successful
        """
        if not self.license_activated:
            validated, msg = activate_license(license_key=self.license_key, account_id=self.account_id)
            if validated:
                self.license_activated = True
                print("\nLicense key was validated and associated with this machine!\n")
                new_license_file = dict(Key=self.license_key, Activated=True, AccountID=self.account_id)
                with open("settings/LicenseKey.json", "w") as file:
                    json.dump(new_license_file, file)
                return validated
            else:
                if msg == "license has already been activated on this machine":
                    return True
                else:
                    raise AssertionError("Activation of license failed! Reason: {}".format(msg))

    def retrieve_license_key(self) -> str:
        """
        Validate the user by sending the license key to the server,
        which validates the license for us. We strictly require the 
        license key to be in a file called "LicenseKey.json" in the 
        settings folder. This sends the key and caches said key
        for the remainder of the session.

        ### Inputs:
        - None

        ### Outputs:
        - Returns the license key to be sent for validation on the
          server
        """
        
        if self.license_activated:
            return self.license_key
        else:
            raise AssertionError("Error! License was not activated!")

    def connect(self) -> bool:
        """
        Connect to the SWARM Server using a standard socket, which is 
        more cross platform then having to install different libraries.

        ### Inputs:
        - None

        ### Outputs
        """
        try:
            self.socket = socket.socket()
            self.socket.connect((self.address, self.port))
            # self.socket.setblocking(False)
            self.connected = True
            return True
        except Exception as error:
            print(error)
            exit(1)
            return False

    def send_message(self, message: str) -> bool:
        """
        Send a message to the SWARM Server. This is a base method to
        build a set of procedural calls on.

        ### Inputs:
        - message[str] the message to send

        ### Outputs
        - A boolean on whether the message was sent successfully
        """
        try:
            if self.connected:
                # Send a header packet containing the information about the
                # message to come.
                header_packet = dict(ID=self.message_id,
                                     Type="Singular",
                                     Body={
                                         "Bytes": len(message)
                                     })
                print("DEBUG Sent header packet")
                self.socket.send(
                    json.dumps(header_packet).encode(ENCODING_SCHEME))
                # Don't immediately step on the socket. Give it some room to
                # breathe
                time.sleep(0.05)
                print("Sending message")
                self.socket.send(message)
                return True
            else:
                raise ConnectionError("Client is no longer connected")
        except ConnectionError:
            traceback.print_exc()
            print("Connection failed")
            return False
        
    def send_multipart_file(self, message_id: int, file_name: str) -> None:
        """
        Send a multipart file that has already been encoded in bytes.

        # Inputs:
        - message [dict] The initial message describing what to send.

        # Outputs:
        - None
        """
        print("Sending multipart file to User")
        start_message = {"ID": message_id,
                         "Type": "Multipart",
                         "Body": {
            "Number Of Bytes": 0,
            "Number Of Packets": 0,
            "LicenseKey": self.retrieve_license_key(),
            "MachineID": self.machine_id
        }}
        with open(file_name, "rb") as file:
            raw_bytes = file.read()

        start_message["Body"]["Command"] = "Load Model"
        # We need full paths for the file name to start:
        # Example: models/SSD.tar.gz but we only want the name of the tar
        # file to be sent. So, always take the last part of the file name
        start_message["Body"]["FileName"] = file_name.split("/")[-1]

        start_message["Body"]["PacketSize"] = MAX_PACKET_SIZE
        start_message["Body"]["Number Of Packets"] = (
            int(len(raw_bytes) / MAX_PACKET_SIZE)) + 1
        start_message["Body"]["Number Of Bytes"] = len(raw_bytes)
        chunks = [raw_bytes[(i * MAX_PACKET_SIZE):(i * MAX_PACKET_SIZE) + MAX_PACKET_SIZE]
                  for i in range(int(len(raw_bytes) / MAX_PACKET_SIZE) + 1)]
        # extra_bytes = int(start_message["Body"]["Number Of Packets"]/10) * 20 + int(start_message["Body"]["Number Of Packets"] % 10) * 1
        # start_message["Body"]["Number Of Bytes"] += extra_bytes
        encoded_message = json.dumps(start_message).encode(self.encoding)
        
        # Don't immediately step on the socket. Give it some room to
        # breathe
        time.sleep(0.1)
        self.send_message(encoded_message)
        print("DEBUG Sent header message")
        time.sleep(0.5)
        for i, chunk in enumerate(chunks):
            try:
                #print("DEBUG: Sending chunk {}".format(i))
                # chunk = bytes("{}".format(i), encoding=self.encoding) + chunk
                sent = self.socket.sendall(chunk)
                # assert sent == MAX_PACKET_SIZE
                # Sleep for 20 milliseconds on each message
                # time.sleep(0.005)
            except BlockingIOError:
                chunk_not_sent = False
                retries = 0
                while not chunk_not_sent or (retries < 50):
                    try:
                        # Resource temp Unavailable
                        # time.sleep(0.01)
                        self.socket.send(chunk)
                        chunk_not_sent = True
                    except BlockingIOError:
                        retries += 1
                    except ConnectionResetError:
                        break
            except AssertionError:
                print("Sent {} of {} bytes".format(sent, MAX_PACKET_SIZE))
                self.socket.send(chunk[sent:])

        return True

    def wait_for_response_packet(self, message_id: int) -> dict:
        """
        Once we send a message, wait for the response from the server.

        ### Inputs:
        - message_id [int] The id of the message that was sent

        ### Outputs:
        - The returned data as a dictionary, indicating a JSON packet
        """
        print(message_id)
        response_completed = False
        received_message = None
        received_header = False
        received_bytes = b''
        total_bytes = 0
        message = None
        while not response_completed:
            try:
                message = self.socket.recv(BUFFER_SIZE)
                if received_header:
                    received_bytes += message
                    if len(received_bytes) < total_bytes:
                        continue
                    else:
                        message = received_bytes

                message = json.loads(message.decode(ENCODING_SCHEME))
                # print(message)
                if not received_header:
                    is_header = "Bytes" in message["Body"].keys()
                    if is_header:
                        total_bytes = message["Body"]["Bytes"]
                        received_header = True
                        continue

                if int(message["ID"]) == message_id:
                    print(message["ID"])
                    print("Received the response message from the server")
                    received_message = message["Body"]
                    print(received_message)
                    response_completed = True
                    self.message_map[str(message_id)]["Completed"] = True
                else:
                    received_header = False
                    received_bytes = b''
                    total_bytes = 0
                    if "Status" in message['Body'].keys():
                        print(message["Body"]["Status"])
                    if "ValidationResults" in message["Body"].keys():
                        print("User Code has been Validated")
                        for agent, feedback in message["Body"]["ValidationResults"].items():
                            print("Code Feedback for {}".format(agent))
                            for module_name, statement in feedback.items():
                                print("\n\nModule: {} \n\n".format(module_name))
                                print(statement)
                    if "Error" in message["Body"].keys():
                        error = message["Body"]["Error"]
                        if error == "Critical":
                            print("ERROR! {}".format(error))
                            assert AssertionError("Received a critical error!")
                    
                    # assert ValueError("Unknown message id!")
            except BlockingIOError:
                # Ensure this thread does not cause the computer
                # to take off!
                time.sleep(0.001)
            except AssertionError as error:
                print("Critical Error occurred!")
                print(error)
                break
            except OSError as error:
                print(error)
                break
            # except KeyboardInterrupt:
            #     self.socket.close()
            #     break
            except JSONDecodeError:
                pass
                # print("DEBUG JSON Decoding Error")
                # if message is not None:
                #     print(message.decode(ENCODING_SCHEME))
                # self.socket.close()
                # break
            except Exception:
                if message is not None:
                    print(message)
                traceback.print_exc()

        if received_message == None:
            assert ValueError("We did not receive a message in the response")
        return received_message

    def wait_for_response_bytes(self, message_id: int) -> bytearray:
        """
        Once we send a message, wait for the response from the server.

        ### Inputs:
        - message_id [int] The id of the message that was sent

        ### Outputs:
        - A raw byte string to be turned into another data type
        """
        response_completed = False
        received_bytes = b''
        while not response_completed:
            try:
                message = self.socket.recv(BUFFER_SIZE)
                message = json.loads(message.decode(ENCODING_SCHEME))
                if message["ID"] == message_id:
                    if message["Type"] == "Multipart":
                        received_bytes = self.handle_multipart(message)
                    else:
                        print(message["Body"])
                        # received_bytes = message["Body"]["Data"]
                    response_completed = True
                    self.message_map[str(message_id)]["Completed"] = True
                else:
                    assert ValueError("Unknown message id!")
            except BlockingIOError:
                pass
            except Exception:
                traceback.print_exc()
                print(message.decode(ENCODING_SCHEME))
                # exit(1)
                # traceback.print_exc()

        return received_bytes

    def handle_multipart(self, message: dict) -> bytes:
        """
        Handle receipt of a multi-part message when transferring data.
        We define multi-part as the first message received and some
        number of subsequent messages containing the raw bytes.

        ### Inputs:
        - message [dict] the start message

        ### Outputs:
        - received bytes
        """
        if self.debug:
            print("DEBUG: Handing Multipart Message")
        numb_packets = message["Body"]["Number Of Packets"]
        total_bytes = message["Body"]["Number Of Bytes"]
        recv_bytes = list()
        total_recv_bytes = 0
        print("Downloading {} bytes".format(total_bytes))

        if self.debug:
            print(f"DEBUG: Packets to download {numb_packets}")
        
        with tqdm(unit="B", unit_scale=True, desc="Data Tarball", total=total_bytes) as bar:
            while total_recv_bytes < total_bytes:
                try:
                    new_bytes = self.socket.recv(BUFFER_SIZE)
                    recv_bytes.append(new_bytes)
                    total_recv_bytes += len(new_bytes)
                    bar.update(len(new_bytes))

                except BlockingIOError:
                    pass
                except Exception:
                    traceback.print_exc()

        # Ensure we have received the full message
        #  assert total_bytes == bytes_received

        recv_data = b''.join(recv_bytes)
        return recv_data

    def _retrieve_loaded_models_from_server(self) -> list:
        """
        Retrieve the previously loaded modules from the server. We want
        to ensure that we are as efficient as possible when handling
        User code and the uploading process, since we could be
        transferring a significant amount of data.

        ### Inputs:
        - None

        ### Outputs:
        - A list of models
        """
        message = dict(ID=self.message_id,
                       Type="Singular",
                       Body={
                                "Command": "Retrieve Loaded Models",
                                "LicenseKey": self.retrieve_license_key(),
                                "MachineID": self.machine_id
                            })
        self.message_map[str(self.message_id)] = {
                "Completed": False,
                "ID": str(self.message_id)
            }
        sent = self.send_message(json.dumps(message).encode(ENCODING_SCHEME))
        if sent:
            # We are waiting for a message that contains a Body with the following
            # information:
            # {
            #   "Body": {
            #       "Models": ["SSD"],
            #       "Errors": []
            #   }
            # }
            data = self.wait_for_response_packet(self.message_id)

            print("DEBUG Models message: {}".format(data))
            self.message_map[str(self.message_id)]["Completed"] = True
            # Increment the next message ID
            if message["ID"] == self.message_id and len(data["Errors"]) == 0:
                self.message_id += 1
                return data["Models"]
            else:
                print("Error while retrieving loaded models")
                for error in data["Errors"]:
                    print(f"\n{error}")
                print("\nPlease try again!")
                self.message_id += 1

                return None
        
        self.message_id += 1
        return None


    def load_user_code(self, settings: dict, path: str = ".") -> str:
        """
        Load and prepare the User Code for sending. This entails reading
        the Python files, encoding them to JSON strings and providing
        that information to the message.

        ### Inputs:
        - settings [dict] The User defined settings of the Agents
        """
        user_code = dict()
        loaded_models = None
        cycle_connection = False
        for agent_name, agent_info in settings["Agents"].items():
            user_code[agent_name] = dict()
            for module_name, module in agent_info["SoftwareModules"].items():
                # Determine that this module can load custom models, where we first
                # check if the User has listed any models that will be used.
                if "Parameters" in module.keys() and "Model" in module["Parameters"].keys() and self._query_custom_model_module_list(module_name):
                    if loaded_models is None:
                        self.connect()
                        loaded_models = self._retrieve_loaded_models_from_server()
                        # If we fail to retrieve the loaded models, then
                        # cancel the valdiation process
                        self.socket.close()
                        time.sleep(1.0)
                        self.connected = False
                        if loaded_models == None:
                            exit(1)
                    # Check if the model has already been tared for loading
                    if  module["Parameters"]["Model"] not in loaded_models:
                        tar_file_name = self._generate_model_tar_file(module["Parameters"]["Model"])
                        self.connect()
                        sent = self.send_multipart_file(self.message_id, tar_file_name)
                        
                        time.sleep(1.0)
                        self.connected = False
                        self.message_map[str(self.message_id)] = {
                            "Completed": False,
                            "ID": str(self.message_id)
                        }
                        return_message = self.wait_for_response_packet(self.message_id)
                        self.socket.close()
                        if sent:
                            self.message_id += 1
                        loaded_models = return_message["Models"]
                    else:
                        tar_file_name = "{}.tar.gz".format(module["Parameters"]["Model"])
                        
                    user_code[agent_name][module_name] = {"Code": tar_file_name, "Model": True, "AlgorithmName":  module["Algorithm"]["ClassName"]}
                else:
                    # If we don't have an algorithm for this module, we bypass
                    # this part of the system.
                    if "Algorithm" not in module.keys():
                        continue
                    isCustomModule, isCustomAlgo = self.query_supported_module_list(module_name, module["Algorithm"]["ClassName"])
                    if isCustomAlgo:
                        with open("{}/user_code/{}/{}.py".format(path, agent_name,  module["Algorithm"]["ClassName"]), "r") as file:
                            user_code[agent_name][module_name] = {"Code": json.dumps(file.read()), "Model": False, "AlgorithmName":  module["Algorithm"]["ClassName"]}
                    elif isCustomModule:
                        with open("{}/user_code/{}/{}.py".format(path, agent_name, module_name), "r") as file:
                            user_code[agent_name][module_name] = {"Code": json.dumps(file.read()), "Model": False, "AlgorithmName": module["Algorithm"]["ClassName"]}

        return user_code

    def _generate_model_tar_file(self, model_name: str) -> str:
        """
        Generate a Tarball to deliver to the Server to be installed.

        ### Inputs:
        - model_name [str] The name of the folder to load

        ### Outputs:
        - The tar file name
        """
        if sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):
            pass
        else:
            subprocess.run(["tar", "-czvf", "models/{}.tar.gz".format(model_name), "models/{}".format(model_name)])
        
        return "models/{}.tar.gz".format(model_name)

    def _query_custom_model_module_list(self, module_name: str) -> bool:
        """
        Check if the module that is being submitted is capable of
        running custom machine learning models.

        ### Inputs:
        - module_name [str] The name of the overall module to load

        ### Output:
        - A boolean flag that says whether the module is available for
          this feature.
        """
        with open("core/SupportedSoftwareModules.json", "r") as file:
            supported_modules = json.load(file)["SupportedModules"]

        # If the User is defining a new module that we don't know the
        # name of.
        if module_name not in supported_modules["ValidCustomModelModules"]:
            return False

        return True

    def query_supported_module_list(self, module_name: str, class_name: str) -> bool:
        """
        Check in the Supported Module List if the the code should be
        uploaded to the SWARM Server.

        ### Inputs:
        - module_name [str] The name of the module to load
        - class_name [str] The name of the algorithm to load
        """
        print("Querying Supported List")
        print(module_name, class_name)
        with open("core/SupportedSoftwareModules.json", "r") as file:
            supported_modules = json.load(file)["SupportedModules"]

        # If the User is defining a new module that we don't know the
        # name of.
        if module_name not in supported_modules["ValidModuleNames"]:
            return True, True

        # Get the module options of a SWARM Module
        module_options = supported_modules[module_name]
        if class_name not in module_options["ValidClassNames"]:
            return False, True
        
        return False, False

    def send_simulation_execution_package(self,
                                          json_file: dict) -> dict:
        """
        Send the Simulation Execution package, containing the JSON file
        and associated metadata to the server, so the server can
        dispatch the job to the simulation system.

        ### Inputs:
        - json_file [dict] The set of configuration files to send
        - simulation_id [int] The simulation id to be run

        ### Outputs:
        - Confirmation that the message was sent.
        """
        try:
            message_packet = dict(ID=self.message_id,
                                  Type="Singular", Body=None)
            json_file["LicenseKey"] = self.retrieve_license_key()
            json_file["MachineID"] = self.machine_id
            message_packet["Body"] = json_file

            json_str = json.dumps(message_packet).encode(ENCODING_SCHEME)

            self.message_map[str(self.message_id)] = {
                "Completed": False,
                "ID": str(self.message_id)
            }
            print("DEBUG Sending execution message to server")
            sent = self.send_message(json_str)

            completed = self.wait_for_response_packet(self.message_id)
            assert completed
            # Only increment to the next message id if we know the last message
            # was sent.
            if sent:
                self.message_id += 1
            # The server kills the connection after the call
            self.connected = False
            return completed
        except AssertionError:
            print("Simulation failed to be completed!")
            exit(1)
        except Exception as error:
            print(error)
            return False

    def request_environment_schematics(self, supported_levels: list) -> bool:
        """
        Send a request to receive the environment schematics.

        ### Inputs:
        - json_file [str] the raw json file as a dict before sending
        - simulation_id [int] The simulation id to be run

        ### Outputs:
        - Confirmation taht the message was sent.
        """
        try:
            message_packet = dict(ID=self.message_id, Type="Single", Body=None)
            execution_package = dict(LicenseKey=self.retrieve_license_key(),
                                     MachineID=self.machine_id,
                                     levels=supported_levels)
            message_packet["Body"] = execution_package
            self.message_map[str(self.message_id)] = {
                "Completed": False,
                "ID": self.message_id
            }
            json_str = json.dumps(message_packet).encode(ENCODING_SCHEME)
            sent = self.send_message(json_str)
            for level in supported_levels:
                # TODO We should wait for message receipt with a timeout.
                raw_img_bytes = self.wait_for_response_bytes(self.message_id)
                if raw_img_bytes:
                    with open("maps/{}.png".format(level), "wb") as file:
                        file.write(raw_img_bytes)
            # Only increment to the next message id if we know the last message
            # was sent.
            if sent:
                self.message_id += 1
            return True
        except Exception as error:
            print(error)
            return False

    def send_data_extraction_message(self, message: dict) -> None:
        try:
            message_packet = dict(ID=self.message_id, Type="Single", Body=None)
            message["LicenseKey"] = self.retrieve_license_key()
            message["MachineID"] = self.machine_id
            message_packet["Body"] = message
            self.message_map[str(self.message_id)] = {
                "Completed": False,
                "ID": self.message_id
            }
            json_str = json.dumps(message_packet).encode(ENCODING_SCHEME)
            sent = self.send_message(json_str)
            # wait for the message that says we are going to get the
            # message
            # self.wait_for_response_packet(self.message_id)
            # TODO We should wait for message receipt with a timeout.
            raw_img_bytes = self.wait_for_response_bytes(self.message_id)
            if raw_img_bytes:
                dirs = os.listdir(".")
                if not "data" in dirs:
                    os.makedirs("data")
                    # subprocess.run(["mkdir", "-p", "{}/data".format(os.getcwd())])
                # TODO Make this either a tar of a zip file
                with open("{}/data/{}_data.tar.gz".format(os.getcwd(), message["SimName"]), "wb") as file:
                    file.write(raw_img_bytes)
                
                os.system("tar -xf {}/data/{}_data.tar.gz -C {}/data && rm {}/data/{}_data.tar.gz".format(os.getcwd(), message["SimName"], os.getcwd(), os.getcwd(), message["SimName"]))
            # Only increment to the next message id if we know the last message
            # was sent.
            if sent:
                self.message_id += 1
            self.connected = False
            print("Data download complete! Please see the Data folder!")
            return True
        except Exception:
            traceback.print_exc()
            return False

    def send_supported_envs_message(self, message: dict) -> None:
        """
        Send a request to the server to retrieve the supported
        environments for the SWARM container.

        ### Inputs:
        - None

        ### Outputs:
        - A file called `SupportedEnvironments.json` will be available
          to view.
        """
        try:
            message_packet = dict(ID=self.message_id,
                                  Type="Singular", Body=None)

            message_packet["Body"] = {
                "Command": "Supported Environments",
                "LicenseKey": self.retrieve_license_key(),
                "MachineID": self.machine_id
            }
            json_str = json.dumps(message_packet).encode(ENCODING_SCHEME)

            self.message_map[str(self.message_id)] = {
                "Completed": False,
                "ID": str(self.message_id)
            }
            sent = self.send_message(json_str)

            completed = self.wait_for_response_packet(self.message_id)
            assert completed
            # Only increment to the next message id if we know the last message
            # was sent.
            if sent:
                self.message_id += 1
            self.connected = False
            return completed
        except AssertionError:
            print("Simulation failed to completed!")
            exit(1)
        except Exception as error:
            print(error)
            return False

    def send_env_information_message(self, message: dict) -> None:
        try:
            message_packet = dict(ID=self.message_id, Type="Single", Body=None)
            message["LicenseKey"] = self.retrieve_license_key()
            message["MachineID"] = self.machine_id
            message_packet["Body"] = message
            self.message_map[str(self.message_id)] = {
                "Completed": False,
                "ID": self.message_id
            }
            json_str = json.dumps(message_packet).encode(ENCODING_SCHEME)
            sent = self.send_message(json_str)
            # wait for the message that says we are going to get the
            # message
            # self.wait_for_response_packet(self.message_id)
            # TODO We should wait for message receipt with a timeout.
            raw_img_bytes = self.wait_for_response_bytes(self.message_id)
            if raw_img_bytes:
                with open("maps/map_data.tar.gz", "wb") as file:
                    file.write(raw_img_bytes)
            # Only increment to the next message id if we know the last message
            # was sent.
            if sent:
                self.message_id += 1
            self.connected = False
            return True
        except Exception:
            traceback.print_exc()
            return False

    def send_user_code_for_validation(self, message: dict, settings: dict) -> bool:
        """
        Send the User's Code for Validation. This should be run before
        each Simulation that contains custom User code, which will
        be auto-detected by the Code Validation system.
        """
        try:
            message_packet = dict(ID=self.message_id, Type="Single", Body=None)
            message["LicenseKey"] = self.retrieve_license_key()
            message["MachineID"] = self.machine_id
            message["Settings"] = json.dumps(settings)
            message["UserCode"] = self.load_user_code(settings=settings)
            message_packet["Body"] = message
            self.message_map[str(self.message_id)] = {
                "Completed": False,
                "ID": self.message_id
            }
            json_str = json.dumps(message_packet).encode(ENCODING_SCHEME)
            sent = self.send_message(json_str)
            # wait for the message that says we are going to get the
            # message
            # self.wait_for_response_packet(self.message_id)
            # TODO We should wait for message receipt with a timeout.
            response = self.wait_for_response_packet(self.message_id)
            self.last_response = response
            print("Validation Results:\n")
            print(response["Body"]["ValidationResults"])
            # Only increment to the next message id if we know the last message
            # was sent.
            if sent:
                self.message_id += 1
            self.connected = False
            return True
        except Exception:
            traceback.print_exc()
            return False


if __name__ == "__main__":
    client = SWARMClient("test")
    client.connect()
    completed = client.request_environment_schematics(["test_received"])
    assert completed
    # test_message = {"ID": 0, "Body": {"Settings": None}}
    # client.send_message(json.dumps(test_message).encode('utf-8'))
