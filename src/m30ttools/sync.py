"""Synchronization utilities

We assume you use airdata.com to retrieve flight information.

This submodule contains some utility functions to synchronize the captured
videos and flight data.
"""

import cv2
import pandas as pd
import numpy as np

from numpy.typing import NDArray
from collections.abc import Generator

from typing import TypedDict
import math


class Geoposition(TypedDict):
    latitude: float
    """Latitude in degrees"""

    longitude: float
    """Longitude in degrees"""

    ground_level_altitude: float
    """Ground altitude in meters"""

    sea_level_altitude: float
    """Absolute altitude in meters"""


class Gimbal(TypedDict):
    pitch: float
    """Pitch angle in degrees"""

    roll: float
    """Roll angle in degrees"""

    yaw: float
    """Yaw angle in degrees"""


class Camera(TypedDict):
    model: str
    """Camera model"""

    focal_length: float
    """Focal length in millimeters"""

    sensor_width: float
    """Sensor width in millimeters"""

    sensor_height: float
    """Sensor height in millimeters"""

    gimbal: Gimbal
    """Gimbal angles"""


class Frame(TypedDict):
    array: NDArray[np.uint8]
    """Frame as a numpy array"""

    timestamp: str
    """Timestamp (ISO 8601) of the frame in the video"""

    geoposition: Geoposition
    """Geoposition of the drone when the frame was captured"""

    camera: Camera
    """Camera information"""


def extract_frames(videos: list[str], fdata: list[str]) -> Generator[Frame, None, None]:
    """Extract frames from videos and synchronize them with flight data

    Videos and flight data are assumed to be ordered by collection time.
    Also, we assume they match and no video (or flight data) is missing.
    These properties are not checked by this function.

    Parameters
    ----------
    videos : list[str]
        List of paths to videos
    fdata : list[str]
        List of paths to flight data

    Returns
    -------
    Generator[Frame, None, None]
        A generator that yields frames
    """

    # Load all datafiles in a single dataframe
    fdata = pd.concat([pd.read_csv(filename) for filename in fdata])

    # Every time the variable isVideo changes (from 0 to 1), we know a new
    # video exists. We can use this to split the dataframe into multiple data
    # frames that match each video.

    # Find the indices where the variable isVideo changes
    indices = np.where(np.diff(fdata.isVideo) == 1)[0]

    print(indices)
    assert len(indices) == len(videos)

    # Split the dataframe into multiple dataframes
    fdata = np.vsplit(fdata, indices)

    # Now remove all rows that are not related to the video, that is, remove
    # rows such that isVideo is 0
    fdata = [df[df.isVideo == 1] for df in fdata]
    fdata = [df for df in fdata if df.shape[0] > 0]

    # The column "time(millisecond)" of each dataframe must start at 0
    for df in fdata:
        df["time(millisecond)"] -= df["time(millisecond)"].iloc[0]

    # Now we can iterate over the videos and synchronize them with the flight
    for i in range(len(videos)):
        # Load the video
        cap = cv2.VideoCapture(videos[i])

        for _, row in fdata[i].iterrows():
            timestamp = row["time(millisecond)"]

            # Seek to the frame
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp)
            ret, frame = cap.read()

            geoposition = {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "ground_level_altitude": row["height_sonar(feet)"],
                "sea_level_altitude": row["altitude_above_seaLevel(feet)"],
            }

            # Convert feet to meters
            geoposition["ground_level_altitude"] *= 0.3048
            geoposition["sea_level_altitude"] *= 0.3048

            # TODO: retrieve camera information from the video file

            camera = {
                "model": "(unknown)",
                "focal_length": math.nan,
                "sensor_width": math.nan,
                "sensor_height": math.nan,
                "gimbal": {
                    "pitch": row["gimbal_pitch(degrees)"],
                    "roll": row["gimbal_roll(degrees)"],
                    "yaw": row["gimbal_heading(degrees)"],
                },
            }

            # Create the frame
            frame = {
                "array": frame,
                "timestamp": timestamp,
                "geoposition": geoposition,
                "camera": camera,
            }

            yield frame
