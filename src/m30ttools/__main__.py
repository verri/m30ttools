"""Command line utilities for dealing with M30T data.

Some of the main subcommands are:
    extract-frames
        Extract frames from video files associating them with
        flight data.
"""


import argparse
import os
import csv
import cv2
import math
import threading
import queue
import pandas as pd

from .sync import extract_frames
from .db import generate_hdf5_from_sync_frames, create_geotiff_from_jpg


def facing_down(frame):
    """Returns True if the frame is facing down."""
    return -91 <= frame["camera"]["gimbal"]["pitch"] <= -89


def efcommand(args):

    # Creates frame directory if it doesn't exist.
    frame_dir = args.frames_dir
    if not os.path.exists(frame_dir):
        os.makedirs(frame_dir)

    # Open CSV file to write frame information.
    output = args.output

    if args.select == 'all':
        args.select = lambda x: True
    elif args.select == 'facing-down':
        args.select = facing_down

    if args.min_altitude is not None:
        f = args.select
        args.select = lambda frame: f(frame) and frame["geoposition"]["ground_level_altitude"] >= args.min_altitude

    with open(output, 'w') as csvfile:
        fieldnames = ['filename', 'video_filename', 'time', 'datetime', 'latitude', 'longitude',
                      'ground_level_altitude', 'sea_level_altitude',
                      'gimbal_pitch', 'gimbal_roll', 'gimbal_yaw']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        def produce_frames(q: queue.Queue):
            for i, frame in enumerate(extract_frames(args.video, args.data,
                    args.select, args.min_time)):
                q.put((i, frame))
            q.put(None)

        def consume_frames(q: queue.Queue):
            while True:
                v = q.get()
                if v is None:
                    q.task_done()
                    break
                i, frame = v
                save_frame(i, frame)
                q.task_done()

        def save_frame(i, frame):
            # TODO: read number of digits from command line as an optional
            # argument.
            filename = f"{args.frames_dir}/{i:07d}.jpg"

            writer.writerow({
                'filename': filename,
                'video_filename': frame["video_filename"],
                'time': frame["time"],
                'datetime': frame["datetime"].isoformat(),
                'latitude': frame["geoposition"]["latitude"],
                'longitude': frame["geoposition"]["longitude"],
                'ground_level_altitude': frame["geoposition"]["ground_level_altitude"],
                'sea_level_altitude': frame["geoposition"]["sea_level_altitude"],
                'gimbal_pitch': frame["camera"]["gimbal"]["pitch"],
                'gimbal_roll': frame["camera"]["gimbal"]["roll"],
                'gimbal_yaw': frame["camera"]["gimbal"]["yaw"],
            })

            array = frame["array"]
            array_size = args.array_size

            if args.crop is not None:
                # Crop frame.
                array = array[args.crop[0]:args.crop[1], args.crop[2]:args.crop[3]]

            if array.shape[2] == 3 and array_size[2] == 1:
                array = cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)

            if array.shape[0] != array_size[0] or array.shape[1] != array_size[1]:
                array = cv2.resize(array, (array_size[0], array_size[1]))

            # Save frame to disk asy
            cv2.imwrite(filename, array)

        q = queue.Queue()

        p = threading.Thread(target=produce_frames, args=(q,))
        p.start()

        c = threading.Thread(target=consume_frames, args=(q,))
        c.start()

        p.join()
        c.join()
        q.join()


def h5command(args):

    generate_hdf5_from_sync_frames(args.data, args.output)


def geotiffcommand(args):

    # Read CSV file
    df = pd.read_csv(args.data)

    for _, row in df.iterrows():
        filename = row['filename']
        create_geotiff_from_jpg(filename, args.output_dir, args.dfov, row)


def main():
    parser = argparse.ArgumentParser(
        prog='m30ttools', description='Tools to organize data from DJI M30T')
    subparsers = parser.add_subparsers(required=True)

    efparser = subparsers.add_parser('extract-frames',
                                     help='Extract frames from video files associating them with flight data.')

    # The first argument of the subcommand extract-frames is a list of video
    # files.
    efparser.add_argument('--video-files', dest='video', nargs='+',
                          help='Video files to extract frames from (order matters).', required=True)

    # The, we need a list of CSV files containing the flight data.
    efparser.add_argument('--flight-data', dest='data', nargs='+',
                          help='CSV files containing flight data (order matters).', required=True)

    # The output directory is where the frames will be saved.
    efparser.add_argument('--frames-dir', dest='frames_dir',
                          help='Directory where to save the extracted frames.', required=True)

    # The minimum time between frames (milliseconds).  If the time between two frames is less
    # than this value, the frame will be discarded.
    efparser.add_argument('--min-time', dest='min_time', type=float, default=0.0)

    # Frame cropping options. The frame will be cropped to the specified
    # dimensions.
    efparser.add_argument('--crop', dest='crop', nargs=4, type=int, default=None)

    # The output CSV file is where the flight data synced with each frame will
    # be saved.
    efparser.add_argument('--output', dest='output',
                          help='CSV file where to save the flight data synced with each frame.', required=True)

    # An option to select which frames will be extracted.  The options are
    # 'all' and 'facing-down'.
    efparser.add_argument('--select', dest='select',
                          default=None, choices=['all', 'facing-down'])

    # An option to filter frames with low altitude.
    efparser.add_argument('--min-altitude', dest='min_altitude', type=float,
            default=None)

    efparser.add_argument(
        '--array-size',
        dest='array_size',
        help='Size of the frame to store.',
        nargs=3,
        type=int,
        default=(160, 90, 3))

    efparser.set_defaults(func=efcommand)

    h5parser = subparsers.add_parser('h5store',
                                     help='Store flight data in HDF5 format.')

    h5parser.add_argument('--flight-data', dest='data',
                          help='CSV filename containing synced flight data.', required=True)

    h5parser.add_argument(
        '--output',
        dest='output',
        help='HDF5 filename where to save the flight data.',
        required=True)

    h5parser.set_defaults(func=h5command)

    # XXX: at the moment, only facing-down is supported.
    geotiffparser = subparsers.add_parser('geotiff',
                                         help='Generate GeoTIFF files from synced flight data.')

    geotiffparser.add_argument('--flight-data', dest='data',
                               help='CSV filename containing synced flight data.', required=True)

    geotiffparser.add_argument('--output-dir', dest='output_dir',
                               help='Directory where to save the GeoTIFF files.', required=True)

    geotiffparser.add_argument('--dfov', dest='dfov', type=float,
                               help='Diagonal field of view of the camera in degrees.', required=True)

    geotiffparser.set_defaults(func=geotiffcommand)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
