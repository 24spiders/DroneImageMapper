# -*- coding: utf-8 -*-
"""
Created on Tue May 20 15:31:58 2025

@author: Labadmin
"""
import re
from datetime import datetime


def dms_to_epsg4326(lat_str, lon_str):
    """
    Converts GPS coordinates from DMS format with cardinal directions to EPSG:4326 (decimal degrees).
    Args:
        coord_str (str): GPS coordinate string, e.g., "53 deg 24' 29.32\" N, 113 deg 58' 50.36\" W"
    Returns:
        coords (tuple): Tuple of (latitude, longitude) in decimal degrees (float)
    """
    def parse_dms(dms_str):
        # Regular expression to extract degrees, minutes, seconds, and direction
        pattern = r'(\d+)\s*deg\s*(\d+)\'\s*([\d.]+)"\s*([NSEW])'
        match = re.match(pattern, dms_str.strip())
        if not match:
            raise ValueError(f'Invalid DMS format: {dms_str}')

        # Extract components
        degrees = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        direction = match.group(4)

        # Convert to decimal degrees
        decimal = degrees + minutes / 60 + seconds / 3600

        # Apply sign based on direction
        if direction in ['S', 'W']:
            decimal = -decimal

        return decimal

    # Convert each component
    lat = parse_dms(lat_str)
    lon = parse_dms(lon_str)

    return (lat, lon)


def elapsed_seconds_since_ref(ref_time_str, target_time_str):
    """
    Computes the seconds and fractional seconds elapsed between a reference time and a target time.

    Args:
        ref_time_str (str): Reference time in format 'YYYY:MM:DD HH:MM:SS.sssZ'
        target_time_str (str): Target time in format 'YYYY:MM:DD HH:MM:SS.sssZ'

    Returns:
        elapsed (float): Seconds (including fractional part) since reference time
    """
    # Define a helper to convert the nonstandard timestamp into a datetime object
    def parse_custom_timestamp(ts):
        # Strip trailing 'Z' and split date and time
        date_part, time_part = ts.strip('Z').split()
        # Replace colons in date with dashes to make it ISO-compatible
        date_part = date_part.replace(':', '-')
        # Combine into standard ISO format
        iso_str = f'{date_part}T{time_part}'
        # Parse the string with millisecond precision
        return datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%S.%f')

    # Parse both timestamps
    ref_dt = parse_custom_timestamp(ref_time_str)
    target_dt = parse_custom_timestamp(target_time_str)

    # Compute time difference in seconds (float includes fractional seconds)
    elapsed = (target_dt - ref_dt).total_seconds()

    return str(elapsed)


def get_first_second_indices(frames):
    """
    Returns indices corresponding to the first occurrence of each unique integer second in the dictionary keys.

    Args:
        time_dict (dict): Dictionary with keys in 'SS.ss' format (e.g., '45.02')

    Returns:
        first_indices (list of int): Indices where each SS appears for the first time
    """
    # Set to track which seconds have been seen
    seen_seconds = set()
    # List to collect indices of first occurrences
    first_indices = []
    first_keys = []

    # Iterate over dictionary keys with index
    for idx, key in enumerate(frames.keys()):
        # Extract the integer seconds part from the key
        second_str = key.split('.')[0]
        # Only add index if this second has not been seen
        if second_str not in seen_seconds:
            seen_seconds.add(second_str)
            first_indices.append(idx)
            first_keys.append(key)

    return first_indices, first_keys


def filter_dict_by_keys(frames, frame_keys):
    # Create a new dictionary with filtered values
    filtered_frames = {key: frames[key] for key in frame_keys}
    return filtered_frames
