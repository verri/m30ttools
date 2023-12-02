import numpy as np

from numpy.typing import NDArray
from typing import TypedDict


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
    video_filename: str
    """Video filename"""

    array: NDArray[np.uint8]
    """Frame as a numpy array"""

    time: int
    """Time (in milliseconds) of the frame in the video"""

    geoposition: Geoposition
    """Geoposition of the drone when the frame was captured"""

    camera: Camera
    """Camera information"""
