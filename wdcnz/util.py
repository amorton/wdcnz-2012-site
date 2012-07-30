"""Utilities for working with dates and times"""

import datetime
import time

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
DISPLAY_FORMAT = "%A %d/%m/%Y %H:%M:%S"

def timestamp_desc(iso_timestamp):
    
    dt = datetime.datetime.strptime(iso_timestamp, ISO_FORMAT)
    return dt.strftime(DISPLAY_FORMAT)
    