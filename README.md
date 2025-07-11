# hydrophone_streamer
A command line tool to rapidly fetch the latest data from various hydrophone sources. 

## Installation
Requirements: 
- python 3 environment
- ffmpeg [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

```pip install git+https://github.com/bnestor/hydrophone_streamer.git```

To edit or add your own data sources:

```
git clone https://github.com/bnestor/hydrophone_streamer.git
cd hydrophone_streamer
pip install -e .
```


## Usage
You may need to get a token from Ocean Networks Canada if you wish to download data from their servers. According to [the documentation](https://wiki.oceannetworks.ca/display/O2A/API+Reference), users should generate the token by "logging in at [http://data.oceannetworks.ca/Profile](http://data.oceannetworks.ca/Profile). Click the "Web Services" tab, then click "Generate Token" "

Then you may set your token by running the command:
```
hydrophone-streamer-set-token ONC_token=<your_token_here> # this only needs to be done once
```



Open up a terminal or command prompt and type:
```
# for ONC you must specify the device code
hydrophone-streamer save_dir=/home/user/Downloads/onc_stream_ICLISTENHF6095 stream_setting={'deviceCode':'ICLISTENHF6095'} hydrophone_network="onc"

# for OOI you must specify a url
hydrophone-streamer save_dir=/home/user/Downloads/ooi_stream stream_setting={'url':'https://rawdata-west.oceanobservatories.org/files/CE02SHBP/LJ01D/HYDBBA106/'} hydrophone_network="ooi"
```

## Run with Docker instead
You may download docker desktop here: [https://docs.docker.com/desktop/](https://docs.docker.com/desktop/)

This assumes you have already entered your ONC_TOKEN, alternatively, you can just copy and paste it in place of `$ONC_TOKEN` below.
Please edit `DOWNLOAD_FOLDER` to represent where you would like to save data on your computer.
```
docker build . -t hydrophone_streamer
export $(cat .env | xargs)
export DOWNLOAD_FOLDER=/path/to/storage/
docker run --rm -it -v $DOWNLOAD_FOLDER:/data/ -e ONC_TOKEN=$ONC_TOKEN hydrophone_streamer:latest hydrophone-streamer save_dir=/data/ooi_stream stream_setting={'url':'https://rawdata-west.oceanobservatories.org/files/CE02SHBP/LJ01D/HYDBBA106/'} hydrophone_network="ooi"
docker run --rm -it -v $DOWNLOAD_FOLDER:/data/ -e ONC_TOKEN=$ONC_TOKEN hydrophone_streamer:latest hydrophone-streamer save_dir=/data/onc_stream_ICLISTENHF6095 stream_setting={'deviceCode':'ICLISTENHF6095'} hydrophone_network="onc"
```

## Supported Hydrophone Sources
- Ocean Networks Canada: [https://www.oceannetworks.ca/](https://www.oceannetworks.ca/)
- Ocean Observatories Initiative: [https://oceanobservatories.org/](https://oceanobservatories.org/)

## Coming Soon
- Option to delete older files
- File pointing to the latest downloaded file for streaming

## Contributing
If you have a hydrophone source, create a custom class that inherits from `src/hydrophone_streamer/supported_classes/base_streaming_class.py`. If token-access is required, you may need to modify the `src/configs/token_config.yaml` as well.

