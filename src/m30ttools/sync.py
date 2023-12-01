"""Synchronization utilities

We assume you use airdata.com to retrieve flight information.

This submodule contains some utility functions to synchronize the captured
videos and flight data.
"""


from typing import TypedDict
from numpy.typing import NDArray


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
    array: NDArray[uint8]
    """Frame as a numpy array"""

    timestamp: str
    """Timestamp (ISO 8601) of the frame in the video"""

    geoposition: Geoposition
    """Geoposition of the drone when the frame was captured"""

    camera: Camera
    """Camera information"""


def extract_frames(videos: list[str], data: list[str]) -> list[Frame]:
    """Extract frames from videos and synchronize them with flight data

    Parameters
    ----------
    videos : list[str]
        List of paths to videos
    data : list[str]
        List of paths to flight data

    Returns
    -------
    list[Frame]
        List of frames
    """
    pass
