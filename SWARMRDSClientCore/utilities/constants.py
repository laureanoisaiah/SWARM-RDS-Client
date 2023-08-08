# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
# 
# Created By: Tyler Fedrizzi
# Created On: 6 December 2022
#
# Description: Core Execution of the forward-facing gui
# =============================================================================
# Encoding scheme for sending bytes
ENCODING_SCHEME = 'utf-8'


CAMERA_SETTINGS_DEFAULTS = {
    "PublishPose": False,
    "Enabled": False,
    "X": 0.0,
    "Y": 0.0,
    "Z": 0.0,
    "Yaw": 0.0,
    "Pitch": 0.0,
    "Roll": 0.0,
    "Settings": {
        "ImageType": "Scene",
        "Width": 640,
        "Height": 480,
        "FramesPerSecond": 24.0,
        "FOV_Degrees": 90.0
    }
}