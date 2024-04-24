"""Utilities to generate HDF5 from synchronized data."""


import os
import pandas as pd
import numpy as np
import cv2
import h5py
import rasterio
from geographiclib.geodesic import Geodesic
import math

def generate_hdf5_from_sync_frames(
        csv_filename: str,
        hdf5_filename: str):
    """Generate HDF5 from synchronized data.

    Parameters
    ----------
    csv_filename : str
        CSV filename contained synchronized frames.
    hdf5_filename : str
        Output HDF5 filename.
    """

    # Read CSV file
    df = pd.read_csv(csv_filename)

    # Create HDF5 file
    if os.path.exists(hdf5_filename):
        raise Exception(f'HDF5 file already exists: {hdf5_filename}')

    with h5py.File(hdf5_filename, 'w') as f:
        for _, row in df.iterrows():
            filename = row['filename']
            array = cv2.imread(filename, cv2.IMREAD_UNCHANGED)

            dset = f.create_dataset(filename, data=array)

            for column in df.columns:
                if column != 'filename':
                    dset.attrs[column] = row[column]


def create_geotiff_from_jpg(jpg_image_path, output_dir, dfov, flight_data):
    """Create GeoTIFF from JPG image.

    Parameters
    ----------
    jpg_path : str
        Path to JPG image.

    output_dir : str
        Output directory.

    dfov : float
        Camera diagonal field of view (degrees).

    flight_data : dict
        CSV row from synced flight data.
        Importante fields are:
                    'datetime', 'latitude', 'longitude',
                    'ground_level_altitude', 'sea_level_altitude',
                    'gimbal_pitch', 'gimbal_roll', 'gimbal_yaw'
    """

    if flight_data['gimbal_pitch'] < -91 or flight_data['gimbal_pitch'] > -89:
        # print warning message and returns
        print(f"Skipping {jpg_image_path} because gimbal_pitch is not -90 degrees")
        return

    output_filename = os.path.join(output_dir, os.path.basename(jpg_image_path).replace('.jpg', '.tif'))

    with rasterio.open(jpg_image_path, 'r') as src:
        jpg_image_array = src.read()
        width, height = src.width, src.height
        channels_count = src.count
        channels_indexes = src.indexes

    # Altitude
    h = flight_data['ground_level_altitude']

    # By the sine rule, we have:
    #   d / sin(dfov / 2) = h / sin(90 - dfov / 2)
    # Now, we can solve for d:
    dfov = math.radians(dfov)
    d = h * math.sin(dfov / 2) / math.sin(math.pi / 2 - dfov / 2)

    # Now, we can calculate the position of the corners of the image
    # in the camera coordinate system
    # gimbal_yaw is Yaw angle of the gimbal (degrees). 0 represents north and increases eastward.
    yaw = math.radians(flight_data['gimbal_yaw'])

    # to find the angle of the top right pixel in relation to the center,
    # we use the ratio between width and height
    theta = math.atan(width / height)
    top_right_yaw = math.degrees(yaw + theta)
    # the remaining corners are:
    top_left_yaw = math.degrees(yaw - theta)
    bottom_right_yaw = math.degrees(yaw + math.pi - theta)
    bottom_left_yaw = math.degrees(yaw + math.pi + theta)

    # Now we can calculate the coordinates of the corners, assuming center of
    # the image is at (frame.latitute, flight_data['longitude'])
    geod = Geodesic.WGS84 # Same thing as EPSG:4326
    top_right = geod.Direct(flight_data['latitude'], flight_data['longitude'], top_right_yaw, d)
    bottom_right = geod.Direct(flight_data['latitude'], flight_data['longitude'], bottom_right_yaw, d)
    bottom_left = geod.Direct(flight_data['latitude'], flight_data['longitude'], bottom_left_yaw, d)
    top_left = geod.Direct(flight_data['latitude'], flight_data['longitude'], top_left_yaw, d)

    crs = 'EPSG:4326'
    gcps = [
        rasterio.control.GroundControlPoint(0, 0, top_left['lon2'], top_left['lat2']),
        rasterio.control.GroundControlPoint(width, 0, top_right['lon2'], top_right['lat2']),
        rasterio.control.GroundControlPoint(width, height, bottom_right['lon2'], bottom_right['lat2']),
        rasterio.control.GroundControlPoint(0, height, bottom_left['lon2'], bottom_left['lat2']),
    ]

    transform = rasterio.transform.from_gcps(gcps)

    with rasterio.open(output_filename, 'w', driver='GTiff', width=width,
            height=height, count=channels_count+1, dtype=str(jpg_image_array.dtype),
                       crs=crs, transform=transform) as dst:
        dst.write(jpg_image_array, channels_indexes)
        dst.update_tags(AUTHOR='verri/m30ttools', CAPTURE_TIMESTAMP=flight_data['datetime'])
        # Create alpha band
        alpha = np.full((height, width), 255, dtype=np.uint8)
        dst.write(alpha, 4)
