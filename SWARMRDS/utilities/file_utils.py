# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All rights reserved.
#
# Created By: Tyler Fedrizzi
# Created On: 1 August 2023
#
#
# Description: Utilities for loading and using file
# =============================================================================
import os
import sys


def find_folder_path(folder_name: str) -> str:
    """
    Find the path to the given folder by seraching in different
    directories, going up to 3 levels back
    """
    try:
        folder_path = os.path.join(os.getcwd(), folder_name)
        if os.path.exists(folder_path):
            return folder_path
        else:
            raise FileNotFoundError(
                "Folder not found in the current directory: {}".format(folder_path)
            )
    except FileNotFoundError:
        print("DEBUG Attempting to go back one directory")

    try:
        folder_path = os.path.join(os.getcwd(), "..", folder_name)
        if os.path.exists(folder_path):
            return folder_path
        else:
            raise FileNotFoundError(
                "Folder not found in {} directory: {}".format(folder_name, folder_path)
            )
    except FileNotFoundError:
        print("DEBUG Attempting to go back two directories")

    try:
        folder_path = os.path.join(os.getcwd(), "..", "..", folder_name)
        if os.path.exists(folder_path):
            return folder_path
        else:
            raise FileNotFoundError(
                "Folder not found in {} directory: {}".format(folder_name, folder_path)
            )
    except FileNotFoundError:
        print("DEBUG Attempting to go back three directories")

    try:
        folder_path = os.path.join(os.getcwd(), "..", "..", "..", folder_name)
        if os.path.exists(folder_path):
            return folder_path
        else:
            raise FileNotFoundError(
                "Folder not found in {} directory: {}".format(folder_name, folder_path)
            )
    except FileNotFoundError:
        return ""


def find_file_path(file_name: str, folder: str) -> str:
    """
    Find the given file and folder by searching paths directly
    from where this application is being run.
    """
    try:
        file_path = os.path.join(os.getcwd(), folder, file_name)
        if os.path.exists(file_path):
            return file_path
        else:
            raise FileNotFoundError(
                "File not found in the current directory: {}".format(file_path)
            )
    except FileNotFoundError:
        print("DEBUG Attempting to go back one directory")

    try:
        file_path = os.path.join(os.getcwd(), "..", folder, file_name)
        if os.path.exists(file_path):
            return file_path
        else:
            raise FileNotFoundError(
                "File not found in {} directory: {}".format(file_name, file_path)
            )
    except FileNotFoundError:
        print("DEBUG Attempting to go back two directories")

    try:
        file_path = os.path.join(os.getcwd(), "..", "..", folder, file_name)
        print("DEBUG File path is {}".format(file_path))
        if os.path.exists(file_path):
            return file_path
        else:
            raise FileNotFoundError(
                "File not found in {} directory: {}".format(file_name, file_path)
            )
    except FileNotFoundError:
        print("DEBUG Attempting to go back three directories")

    try:
        file_path = os.path.join(os.getcwd(), "..", "..", "..", folder, file_name)
        if os.path.exists(file_path):
            return file_path
        else:
            raise FileNotFoundError(
                "File not found in {} directory: {}".format(file_name, file_path)
            )
    except FileNotFoundError:
        return ""