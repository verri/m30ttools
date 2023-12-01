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


def efcommand(args):
    print(args)

    # Creates frame directory if it doesn't exist.
    frame_dir = args.frames_dir
    if not os.path.exists(frame_dir):
        os.makedirs(frame_dir)

    # Open CSV file to write frame information.
    output = args.output

    with open(output, 'w') as csvfile:
        fieldnames = ['filename', 'timestamp', 'latitude', 'longitude',
                      'ground_level_altitude', 'sea_level_altitude',
                      'gimbal_pitch', 'gimbal_roll', 'gimbal_yaw']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Extract frames and write to CSV file.
        for i, frame in enumerate(extract_frames(args.video, args.data)):
            # TODO: read number of digits from command line as an optional
            # argument.
            filename = f"{args.frames_dir}/{i:07d}.jpg"

            writer.writerow({
                'filename': filename,
                'timestamp': frame["timestamp"],
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


def main():
    parser = argparse.ArgumentParser(
        prog='m30ttools', description='Tools to organize data from DJI M30T')
    subparsers = parser.add_subparsers(required=True)

    efparser = subparsers.add_parser('extract-frames',
                                     help='Extract frames from video files associating them with flight data.')

    # The first argument of the subcommand extract-frames is a list of video files.
    efparser.add_argument('--video-files', dest='video', nargs='+',
                          help='Video files to extract frames from (order matters).', required=True)

    # The, we need a list of CSV files containing the flight data.
    efparser.add_argument('--flight-data', dest='data', nargs='+',
                          help='CSV files containing flight data (order matters).', required=True)

    # The output directory is where the frames will be saved.
    efparser.add_argument('--frames-dir', dest='frames_dir',
                          help='Directory where to save the extracted frames.', required=True)

    # The output CSV file is where the flight data synced with each frame will be saved.
    efparser.add_argument('--output', dest='output',
                          help='CSV file where to save the flight data synced with each frame.', required=True)

    efparser.set_defaults(func=efcommand)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
