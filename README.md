# m30ttools

Tools to organize data from DJI M30T

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

