"""
OOI Streaming Class
"""


from hydrophone_streamer.supported_classes.base_streaming_class import BaseStreamingClass

from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import re


import obspy
import glob



class OOIStreamingClass(BaseStreamingClass):
    def __init__(self, hydrophone_identifier: dict, save_dir: str= "data") -> None:
        """
        Initialize the OOIStreamingClass with the hydrophone identifier.

        Args:
            hydrophone_identifier (dict): Dictionary containing hydrophone configuration.
        """
        super().__init__(hydrophone_identifier)
        self.hydrophone_identifier = hydrophone_identifier
        print(self.hydrophone_identifier)
        self.save_dir = save_dir

        self.metadata = {'CE02SHBP': {'latitude': 44.6371, 'longitude': -124.306, 'depth': 79, 'reference_designator':'CE02SHBP-LJ01D-06-CTDBPN106'},
                         'CE04OSBP': {'latitude': 44.3695, 'longitude': -124.954, 'depth': 579 , 'reference_designator':'CE04OSBP-LJ01C-06-DOSTAD108'},
                        'RS01SBPS': {'latitude': 44.529, 'longitude': -125.3893, 'depth': 2906, 'reference_designator':'RS01SBPS-PC01A-4C-FLORDD103'},
                        'RS01SLBS': {'latitude': 44.5153, 'longitude': -125.3898, 'depth': 2901, 'reference_designator':'RS01SLBS-LJ01A-12-DOSTAD101'},
                        'RS03AXBS': {'latitude': 45.8168, 'longitude': -129.7543, 'depth': 2906, 'reference_designator':'RS03AXBS-LJ03A-12-CTDPFB301'},
                        'RS03AXPS': {'latitude': 45.8305, 'longitude': -129.7535, 'depth': 2607, 'reference_designator':'RS03AXPS-PC03A-4A-CTDPFA303'},
        }

        os.makedirs(self.save_dir, exist_ok=True)


        if isinstance(self.hydrophone_identifier, dict):
            print(hydrophone_identifier.keys())

        assert 'url' in self.hydrophone_identifier.keys(), "Hydrophone identifier must contain 'url' key."
                
        self.url = self.hydrophone_identifier['url']

        assert self.url.startswith('https://rawdata-west.oceanobservatories.org/files/'), "URL is not recognised for OOI"
        # assert that url is a valid URL
        response = requests.get(self.url)
        if response.status_code != 200:
            raise ValueError(f"Invalid URL: {self.url}. Status code: {response.status_code}")
        
        deployment = None
        for k in self.metadata.keys():
            if k in self.url:
                deployment = k
                break

        assert deployment is not None, f"Deployment metadata not found for URL: {self.url}"
        self.deployment = deployment

        self.built_in_delay = 30 # minutes


    def _most_recent_file_date(self, return_file: bool = False):
        """
        return the datetime object of the most recent file in the save_dir
        """

        all_files = glob.glob(os.path.join(self.save_dir, '*.flac'))

        # initialize with minimum date time
        max_time = datetime.min
        if max_time.tzinfo is None:
            max_time = max_time.replace(tzinfo=timezone.utc)

        max_file = None
        for file in all_files:

            try:
                this_time = datetime.fromisoformat(re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z', os.path.basename(file)).group(0))
            except:
                this_time = datetime.fromisoformat(re.search(r'\d{4}-\d{2}-\d{2}T\d{2}\d{2}\d{2}\.\d{6}Z', os.path.basename(file)).group(0))
            # this_time = datetime.fromisoformat(this_time)
            if this_time.tzinfo is None:
                this_time = this_time.replace(tzinfo=timezone.utc)
            if this_time > max_time:
                max_time = this_time
                max_file = file

        if return_file:
            return max_time, max_file


        return max_time




    def download_data(self):
        """
        Download data from the OOI hydrophone.

        Returns:
            list: List of fetched results.
        """
        # current time utc
        current_time = datetime.now(timezone.utc)

        # get time 5 minutes ago
        five_minutes_ago = current_time - timedelta(minutes=5)

        built_in_delay = current_time - timedelta(minutes=self.built_in_delay)

        # built in delay as the maximum time between built in delay and _most_recent_file_date
        built_in_delay = max(built_in_delay, self._most_recent_file_date())


        #https://rawdata-west.oceanobservatories.org/files/CE02SHBP/LJ01D/11-HYDBBA106/2018/01/01/

        url_builder = os.path.join(self.url, five_minutes_ago.strftime('%Y/%m/%d/')) # add the extensions to download the files from this date

        response = requests.get(url_builder)

        print(response.status_code, type(response.status_code))

        fetched_results = []

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            assert len(soup.find_all('a'))>0, f"No links found in the response from {url_builder}"

            for link in reversed(soup.find_all('a')):
                href = link.get('href')
                if href.endswith('.mseed'):
                    # for example href is ./OO-HYEA2--YDH-2018-01-01T00:00:00.000000.mseed
                    # and url is https://rawdata-west.oceanobservatories.org/files/CE02SHBP/LJ01D/11-HYDBBA106/2018/01/01/
                    # we want to save the file to os.path.join(base_dir, 'CE02SHBP/LJ01D/11-HYDBBA106/2018/01/01/OO-HYEA2--YDH-2018-01-01T00:00:00.000000.mseed')
                    absolute_url = urljoin(url_builder, href)
                    print(absolute_url)

                    
                    # absolute_url example: https://rawdata.oceanobservatories.org/files/CE02SHBP/LJ01D/HYDBBA106/2025/05/24/OO-HYEA2--YDH-2025-05-24T23:55:00.000000Z.mseed
                    # filter using regex to extract the filename with timestamp
                    filename_timestamp = datetime.fromisoformat(re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z', absolute_url).group(0))

                    # print('filename_timestamp:', filename_timestamp, 
                    #       'built_in_delay:', built_in_delay,
                    #       'current_time:', current_time)

                    if built_in_delay.tzinfo is None:
                        built_in_delay = built_in_delay.replace(tzinfo=timezone.utc)
                    if current_time.tzinfo is None:
                        current_time = current_time.replace(tzinfo=timezone.utc)
                    if filename_timestamp <= built_in_delay:
                        continue
                    if filename_timestamp > current_time:
                        continue

                    d = requests.get(absolute_url)
                    if int(d.headers['Content-Length'])<1000000:
                        continue


                    local_path = os.path.join(self.save_dir, os.path.basename(absolute_url)).replace(':','')
                    # print('local_path:',local_path)


                    # Download the file
                    if not(os.path.exists(local_path) or os.path.exists(local_path.replace('.mseed','.flac'))):
                        # use wget silently and non blocking
                        # print(f'wget -q {absolute_url} -O '+ local_path.replace(" ", "\ ")) 
                        os.system(f'wget -q {absolute_url} -O '+local_path.replace(" ", "\ "))


                        # convert from mseed to flac
                        mseed2flac([local_path],)

                        fetched_results.append(local_path.replace('.mseed','.flac'))

        else:
            raise ValueError(f"Failed to fetch data from {url_builder}. Status code: {response.status_code}")

        if not(os.path.exists(os.path.join(self.save_dir, 'reference.bib'))):
            bibtex=f"""@misc{{{self.metadata[self.deployment]['reference_designator']}_{current_time.strftime('%Y%m%d')},
    'title': 'NSF Ocean Observatories Initiative',
    'year': {datetime.now().strftime('%Y')},
    'howpublished': 'Instrument and/or data product(s) {self.metadata[self.deployment]['reference_designator']} data from {built_in_delay.strftime("%Y-%m-%d")} to {current_time.strftime("%Y-%m-%d")}',
    'publisher': 'Raw Data Archive',
    'url': {url_builder},
    'accessed': {datetime.now().strftime("%Y-%m-%d")},}}"""
        
            with open(os.path.join(self.save_dir, 'reference.bib'), 'w') as f:
                f.write(bibtex)

        return fetched_results
    
    def latest_file(self) -> None:
        """
        Log the most recent audio file to a file for streaming purposes.
        """
        # get the most recent file in the save_dir
        this_time, max_file = self._most_recent_file_date(return_file=True)



        # save the filename in a text file called latest.txt
        with open(os.path.join(self.save_dir, 'latest.txt'), 'w+') as f:
            f.write(max_file.replace(self.save_dir, '').strip('/')) # remove the save_dir and .flac extension

        return




def mseed2flac(filenames):
    # resolve wildcard characters
    # print(filenames)
    if type(filenames)==str:
        if '*' in filenames:
            filenames = glob.glob(filenames, recursive=True)
    else:
        if len(filenames)==1:
            if '*' in filenames[0]:
                filenames = glob.glob(filenames[0], recursive=True)

    # print(filenames)
    # print('here')
    for filename in filenames:
        # print(filename)
        if not(filename.endswith('mseed')):continue
        # print(filename)
        # try:
        st = obspy.read(filename, format='mseed')
        st.merge(fill_value=0)
        sample_rate = st[0].stats['sampling_rate']
        st.write(filename.replace('mseed','wav'), format='WAV', framerate=sample_rate)
        # by default say no to overwrite

        os.system('ffmpeg -n -i '+filename.replace(' ', '\ ').replace('mseed','wav')+' -c:a flac '+filename.replace(' ', '\ ').replace('mseed','flac')+"&& rm "+filename.replace(' ', '\ ').replace('mseed','wav'))
        assert not(os.path.exists(filename.replace(' ', '\ ').replace('mseed','wav'))) # likely no system ffmpeg installed
        

        # os.system('rm '+filename.replace(' ', '\ ').replace('mseed','wav'))
        os.system('rm '+filename.replace(' ', '\ ')) # also remove mseed file




