# Select a base environment
FROM python:3.11-slim AS pyenv

# Install system requirements
RUN apt-get update -y && apt-get install git ffmpeg wget -y

# copy the code into the necessary directory
WORKDIR /hydrophone_streamer

COPY ./ /hydrophone_streamer/


# install the downloader scripts
RUN pip install .



# docker build . -t hydrophone_streamer
# export $(cat .env | xargs)
# export DOWNLOAD_FOLDER=/path/to/storage/
# docker run --rm -it -v $DOWNLOAD_FOLDER:/data/ -e ONC_TOKEN=$ONC_TOKEN hydrophone_streamer:latest hydrophone-streamer save_dir=/data/ooi_stream stream_setting={'url':'https://rawdata-west.oceanobservatories.org/files/CE02SHBP/LJ01D/HYDBBA106/'} hydrophone_network="ooi"
# docker run --rm -it -v $DOWNLOAD_FOLDER:/data/ -e ONC_TOKEN=$ONC_TOKEN hydrophone_streamer:latest hydrophone-streamer save_dir=/data/onc_stream_ICLISTENHF6095 stream_setting={'deviceCode':'ICLISTENHF6095'} hydrophone_network="onc"