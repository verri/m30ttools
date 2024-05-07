# m30ttools

-----

This repo is archived and will probably be deleted soon.

New repo at https://github.com/drone-comp/m30ttools

-----

Tools to organize data from DJI M30T.

Video data is the video files recorded by the drone and stored in the SD card.

Flight data is the data extracted from the airdata.com website.  The following header is assumed:
```
time(millisecond),datetime(utc),latitude,longitude,height_above_takeoff(meters),height_above_ground_at_drone_location(meters),ground_elevation_at_drone_location(meters),altitude_above_seaLevel(meters),height_sonar(meters),speed(m/s),distance(meters),mileage(meters),satellites,gpslevel,voltage(v),max_altitude(meters),max_ascent(meters),max_speed(m/s),max_distance(meters), xSpeed(m/s), ySpeed(m/s), zSpeed(m/s), compass_heading(degrees), pitch(degrees), roll(degrees),isPhoto,isVideo,rc_elevator,rc_aileron,rc_throttle,rc_rudder,rc_elevator(percent),rc_aileron(percent),rc_throttle(percent),rc_rudder(percent),gimbal_heading(degrees),gimbal_pitch(degrees),gimbal_roll(degrees),battery_percent,voltageCell1,voltageCell2,voltageCell3,voltageCell4,voltageCell5,voltageCell6,current(A),battery_temperature(c),altitude(meters),ascent(meters),flycStateRaw,flycState,message
```

You must ensure that the flight data is in the correct units (e.g. meters, meters/second, etc).
(Probably the library will emit an error if the units are incorrect, but I haven't tested it.)

## Installation

```sh
pip install git+https://github.com/verri/m30ttools
```

## Usage

```sh
python -m m30ttools extract-frames \
  --video-files video/*_S.MP4 \
  --flight-data data/*.csv \
  --frames-dir frames \
  --output data.csv
```

