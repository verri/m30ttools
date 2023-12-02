"""Synchronization utilities

We assume you use airdata.com to retrieve flight information.

This submodule contains some utility functions to synchronize the captured
videos and flight data.
"""

import cv2
import pandas as pd
import numpy as np

import math

from collections.abc import Generator

from typing import Callable

from .typing import Frame


def extract_frames(videos: list[str], fdata: list[str], cond: Callable[[
                   Frame], bool] = None) -> Generator[Frame, None, None]:
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
    cond : Callable[[Frame], bool], optional
        A function that takes a frame and returns True if the frame should be
        returned, False otherwise. If None, all frames are returned.

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
            time = row["time(millisecond)"]

            geoposition = {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "ground_level_altitude": row["height_above_ground_at_drone_location(meters)"],
                "sea_level_altitude": row["altitude_above_seaLevel(meters)"],
            }

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
                "video_filename": videos[i],
                "array": None,
                "time": time,
                "geoposition": geoposition,
                "camera": camera,
            }

            if cond is not None and not cond(frame):
                continue

            # Seek to the frame
            cap.set(cv2.CAP_PROP_POS_MSEC, time)
            ret, array = cap.read()

            frame["array"] = array
            yield frame
