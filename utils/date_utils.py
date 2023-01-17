# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All Rights Reserved.
#
# Created By: Tyler Fedrizzi
# Created On: 16 December 2022
#
# Description: Date utils
# =============================================================================
import datetime

def convert_datetime_to_str(date_time):
    format = '%m/%d/%y %H:%M:%S' # The format
    datetime_obj = date_time.strftime(format)

    return datetime_obj


def convert_str_to_datetime(date_time): 
    format = '%m/%d/%y %H:%M:%S' # The format 
    datetime_str = datetime.datetime.strptime(date_time, format) 
   
    return datetime_str