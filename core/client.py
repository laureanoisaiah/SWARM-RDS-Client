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
from tqdm import tqdm

from threading import Thread, Event

from core.validator import activate_license

# from utils.constants import ENCODING_SCHEME
ENCODING_SCHEME = "utf-8"
BUFFER_SIZE = 8192


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
                self.socket.send(
                    json.dumps(header_packet).encode(ENCODING_SCHEME))
                # Don't immediately step on the socket. Give it some room to
                # breathe
                time.sleep(0.05)
                self.socket.send(message)
                return True
            else:
                raise ConnectionError("Client is no longer connected")
        except ConnectionError:
            print("Connection failed")
            return False

    def wait_for_response_packet(self, message_id: int) -> dict:
        """
        Once we send a message, wait for the response from the server.

        ### Inputs:
        - message_id [int] The id of the message that was sent

        ### Outputs:
        - The returned data as a dictionary, indicating a JSON packet
        """
        response_completed = False
        received_message = None
        received_header = False
        received_bytes = b''
        total_bytes = 0
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
                    received_message = message["Body"]
                    response_completed = True
                    self.message_map[str(message_id)]["Completed"] = True
                else:
                    print(message["Body"]["Status"])
                    if "Error" in message["Body"].keys():
                        error = message["Body"]["Error"]
                        if error == "Critical":
                            print("ERROR! {}".format(error))
                            assert AssertionError("Received a critical error!")
                    received_header = False
                    received_bytes = b''
                    total_bytes = 0
                    # assert ValueError("Unknown message id!")
            except BlockingIOError:
                # Ensure this thread does not cause the computer
                # to take off!
                time.sleep(0.001)
            except AssertionError:
                break
            except Exception:
                pass
                # traceback.print_exc()

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
                    print("Blocking IO Error!")
                except Exception:
                    traceback.print_exc()

        # Ensure we have received the full message
        #  assert total_bytes == bytes_received

        recv_data = b''.join(recv_bytes)
        return recv_data

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
                with open("{}/data/{}_data.tar.gz".format(os.getcwd(), message["SimName"]), "wb") as file:
                    file.write(raw_img_bytes)
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

if __name__ == "__main__":
    client = SWARMClient("test")
    client.connect()
    completed = client.request_environment_schematics(["test_received"])
    assert completed
    # test_message = {"ID": 0, "Body": {"Settings": None}}
    # client.send_message(json.dumps(test_message).encode('utf-8'))
