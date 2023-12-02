"""Utilities to generate HDF5 from synchronized data."""


import os
import pandas as pd
import numpy as np
import cv2
import h5py


def generate_hdf5_from_sync_frames(
        csv_filename: str,
        hdf5_filename: str,
        array_shape=(160, 90, 1)):
    """Generate HDF5 from synchronized data.

    Parameters
    ----------
    csv_filename : str
        CSV filename contained synchronized frames.
    hdf5_filename : str
        Output HDF5 filename.
    array_shape :
        Stored array shape.
        Grayscale conversion is done automatically if needed.
    """

    # Read CSV file
    df = pd.read_csv(csv_filename)

    # Create HDF5 file
    if os.path.exists(hdf5_filename):
        raise Exception(f'HDF5 file already exists: {hdf5_filename}')

    with h5py.File(hdf5_filename, 'w') as f:
        for _, row in df.iterrows():
            filename = row['filename']
            array = cv2.imread(filename)

            if array.shape[2] == 3 and array_shape[2] == 1:
                array = cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)

            array = cv2.resize(array, (array_shape[1], array_shape[0]))

            dset = f.create_dataset(filename, data=array)

            for column in df.columns:
                if column != 'filename':
                    dset.attrs[column] = row[column]
