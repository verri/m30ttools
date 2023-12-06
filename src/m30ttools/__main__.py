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

from .sync import extract_frames
from .db import generate_hdf5_from_sync_frames


def facing_down(frame):
    """Returns True if the frame is facing down."""
    return -91 <= frame["camera"]["gimbal"]["pitch"] <= -89


def efcommand(args):
    print(args)

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
        fieldnames = ['filename', 'video_filename', 'time', 'latitude', 'longitude',
                      'ground_level_altitude', 'sea_level_altitude',
                      'gimbal_pitch', 'gimbal_roll', 'gimbal_yaw']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Extract frames and write to CSV file.
        for i, frame in enumerate(extract_frames(
                args.video, args.data, args.select)):
            # TODO: read number of digits from command line as an optional
            # argument.
            filename = f"{args.frames_dir}/{i:07d}.jpg"

            writer.writerow({
                'filename': filename,
                'video_filename': frame["video_filename"],
                'time': frame["time"],
                'latitude': frame["geoposition"]["latitude"],
                'longitude': frame["geoposition"]["longitude"],
                'ground_level_altitude': frame["geoposition"]["ground_level_altitude"],
                'sea_level_altitude': frame["geoposition"]["sea_level_altitude"],
                'gimbal_pitch': frame["camera"]["gimbal"]["pitch"],
                'gimbal_roll': frame["camera"]["gimbal"]["roll"],
                'gimbal_yaw': frame["camera"]["gimbal"]["yaw"],
            })

            # Save frame to disk.
            cv2.imwrite(filename, frame["array"])


def h5command(args):
    print(args)

    generate_hdf5_from_sync_frames(args.data, args.output, args.array_size)


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

    efparser.set_defaults(func=efcommand)

    h5parser = subparsers.add_parser('h5store',
                                     help='Store flight data in HDF5 format.')

    h5parser.add_argument('--flight-data', dest='data',
                          help='CSV filename containing flight data.', required=True)

    h5parser.add_argument(
        '--output',
        dest='output',
        help='HDF5 filename where to save the flight data.',
        required=True)

    h5parser.add_argument(
        '--array-size',
        dest='array_size',
        help='Size of the frame to store.',
        default=(160, 90, 1))

    h5parser.set_defaults(func=h5command)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
