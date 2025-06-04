"""
onc_streaming_class.py
"""


from hydrophone_streamer.supported_classes.base_streaming_class import BaseStreamingClass

from datetime import datetime, timedelta, timezone

import requests
import os
from urllib.parse import urljoin
import re
import json
from copy import deepcopy
import glob

from omegaconf import DictConfig, OmegaConf


from onc.onc import ONC


try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    # assume everything is loaded using export $(cat .env | xargs)
    pass

token = os.getenv('ONC_TOKEN')

def check_token_is_set():
    """
    """
    error_message = """You do not have an Ocean Networks Canada token registered in the repository. To add your token, run
    hydrophone-downloader-set-token ONC_token=<your_token_here>

    This only needs to be done once. If you do not have an ONC token, you can get one by registering at https://data.oceannetworks.ca/Profile and then going to the 'Web Services' tab and clicking "Generate Token".
    """
    assert token is not None, error_message
    assert token != "" , error_message


class ONCStreamingClass(BaseStreamingClass):
    def __init__(self, 
                 hydrophone_identifier: dict,
                 save_dir: str = "data") -> None:
        """
        Initialize the ONCStreamingClass with the hydrophone identifier.

        Args:
            hydrophone_identifier (dict): Dictionary containing hydrophone configuration.
        """
        super().__init__(hydrophone_identifier)
        self.hydrophone_identifier = hydrophone_identifier
        self.save_dir = save_dir

        check_token_is_set()

        


        os.makedirs(self.save_dir, exist_ok=True)

        print(self.save_dir)

        self.onc = ONC(token=token,
                       outPath=self.save_dir,)

        if isinstance(self.hydrophone_identifier, dict):
            print(hydrophone_identifier.keys())

        self.api_url = 'https://data.oceannetworks.ca/api/deployments'

        self.built_in_delay = 60 # minutes, this is the built in delay for the ONC hydrophone data

    def get_citation(self) -> str:
        """
        """
        assert 'deviceCode' in self.hydrophone_identifier.keys(), "Hydrophone identifier must contain 'deviceCode' key."

        parameters = {
            'method': 'get',
            'token': token,
            'deviceCode': self.hydrophone_identifier['deviceCode'],
            'deviceCategoryCode': 'HYDROPHONE',
        }

        response = requests.get(self.api_url, params=parameters)

        if (response.ok):
            deployments = json.loads(str(response.content,'utf-8')) # convert the json response to an object
        else:
            if(response.status_code == 400):
                error = json.loads(str(response.content,'utf-8'))
                print(error) # json response contains a list of errors, with an errorMessage and parameter
            else:
                print ('Error {} - {}'.format(response.status_code,response.reason))


        if not(os.path.exists(os.patj.join(self.save_dir, 'reference.bib'))):
            author, year, title, journal, doi = citation.split('. ')
            citation = "@misc{"+self.save_dir.split('/')[-1]+", author={"+author+"}, year={"+year+"}, title={"+title+"}, journal={"+journal+"}, doi={"+doi+"},}"
            with open(os.path.join(self.save_dir, 'reference.bib'), 'w') as f:
                f.write(citation)


    def _most_recent_file_date(self):
        """
        return the datetime object of the most recent file in the save_dir
        """

        all_files = glob.glob(os.path.join(self.save_dir, '*.flac'))

        # initialize with minimum date time
        max_time = datetime.min
        if max_time.tzinfo is None:
            max_time = max_time.replace(tzinfo=timezone.utc)


        for file in all_files:
            this_time = datetime.fromisoformat(re.search(r'\d{4}\d{2}\d{2}T\d{2}\d{2}\d{2}\.\d{3}Z', os.path.basename(file)).group(0))

            # try:
            #     this_time = datetime.fromisoformat(re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z', os.path.basename(file)).group(0))
            # except:
            #     this_time = datetime.fromisoformat(re.search(r'\d{4}-\d{2}-\d{2}T\d{2}\d{2}\d{2}\.\d{6}Z', os.path.basename(file)).group(0))
            # # this_time = datetime.fromisoformat(this_time)
            if this_time.tzinfo is None:
                this_time = this_time.replace(tzinfo=timezone.utc)
            if this_time > max_time:
                max_time = this_time

        return max_time

        


    def download_data(self) -> list:
        """
        Download data from the ONC hydrophone.

        Returns:
            list: List of downloaded file paths.
        """

         # current time utc
        current_time = datetime.now(timezone.utc)
        # get time 5 minutes ago
        five_minutes_ago = current_time - timedelta(minutes=5)
        built_in_delay = current_time - timedelta(minutes=self.built_in_delay)
        # built in delay as the maximum time between built in delay and _most_recent_file_date
        built_in_delay = max(built_in_delay, self._most_recent_file_date())


        # get omegaconf as dictionary
        filters = self.hydrophone_identifier
        if isinstance(filters, DictConfig) | isinstance(filters, OmegaConf):
            filters = OmegaConf.to_container(filters, resolve=True)

        assert isinstance(filters, dict), "Hydrophone identifier must be a dictionary."

        assert 'deviceCode' in filters.keys(), "Hydrophone identifier must contain 'deviceCode' key."
        filters.update({'extension':'flac',
                       'dateFrom': built_in_delay.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                        'dateTo': current_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                       })


        # i.e. {'deviceCode': 'ICLISTENHF1266', 'dateFrom': '2025-05-25T00:00:00.000Z', 'dateTo': '2025-05-26T00:00:00.000Z', 'extension': 'flac'}

        
        

        filters_archived = filters.copy()
        filters_archived['dateFrom'] = built_in_delay.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        filters_archived['dateTo'] = current_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        filters_archived['rowLimit'] = 80000
        # deviceCode, dateFrom, dateTo, extension, rowLimit
        assert set(list(filters_archived.keys())) == set(['deviceCode', 'dateFrom', 'dateTo', 'extension', 'rowLimit']), "Filters must contain 'deviceCode', 'dateFrom', 'dateTo', 'extension' and 'rowLimit' keys."

        print(filters_archived)
        fetched_results = []
        results = self.onc.getListByDevice(filters_archived)
        if len(results['files'])>0:
            # download the files
            # print(results['files'])
            prev_files = [f for f in results['files'] if os.path.exists(os.path.join(self.save_dir, os.path.basename(f)))]
            if set(results['files']) == set(prev_files):
                # all files have already been downloaded
                return fetched_results
            # print(results)
            result = self.onc.getDirectFiles(filters_archived)
            print('result', result)
            # save the filters to json in fname
            with open(os.path.join(self.save_dir, 'filters.json'), 'w') as f:
                json.dump(filters_archived, f)

            fetched_results = [os.path.join(self.save_dir, os.path.basename(f)) for f in results['files'] if f not in prev_files]


        else:
            # optional parameters to loop through and try:
            # filters_orig = {'locationCode': locationCode,'deviceCategoryCode':'HYDROPHONE','dataProductCode':'AD','extension':'flac','dateFrom':built_in_delay.strftime('%Y-%m-%dT%H:%M:%S.000Z'),'dateTo':current_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),'dpo_audioDownsample':-1} #, 'dpo_audioFormatConversion':0}
            filters_orig = {'deviceCode': filters['deviceCode'],'deviceCategoryCode':'HYDROPHONE','dataProductCode':'AD','extension':'flac','dateFrom':built_in_delay.strftime('%Y-%m-%dT%H:%M:%S.000Z'),'dateTo':current_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),'dpo_audioDownsample':-1} #, 'dpo_audioFormatConversion':0}
            filters_orig = {'locationCode': 'FGPD','deviceCategoryCode':'HYDROPHONE','dataProductCode':'AD','extension':'flac','dateFrom':built_in_delay.strftime('%Y-%m-%dT%H:%M:%S.000Z'),'dateTo':current_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),'dpo_audioDownsample':-1} #, 'dpo_audioFormatConversion':0}

            is_done = False
            for d in [{'dpo_hydrophoneDataDiversionMode':'OD'}, {'dpo_hydrophoneDataDiversionMode':'OD', 'dpo_hydrophoneChannel':'All'},{'dpo_hydrophoneChannel':'All'},{'dpo_audioFormatConversion':0,'dpo_hydrophoneDataDiversionMode':'OD','dpo_hydrophoneChannel':'All'},{'dpo_audioFormatConversion':0,'dpo_hydrophoneDataDiversionMode':'OD'},{'dpo_audioFormatConversion':1,'dpo_hydrophoneDataDiversionMode':'OD','dpo_hydrophoneChannel':'All'}]:
                # for d in [{'dpo_hydrophoneDataDiversionMode':'OD'}, {'dpo_hydrophoneDataDiversionMode':'OD', 'dpo_hydrophoneChannel':'All'},{'dpo_hydrophoneChannel':'All'}]:
                filters = deepcopy(filters_orig)
                filters.update(d)
                try:
                    print(filters)
                    result  = self.onc.orderDataProduct(filters, includeMetadataFile=False)
                    # save the filters to json in fname
                    with open(os.path.join(self.save_dir, 'filters.json'), 'w') as f:
                        json.dump(filters, f)
                    is_done=True
                    break
                except:
                    continue

        if filters['extension'] == 'wav':
            os.system('for s in '+self.save_dir.replace(' ', '\ ')+'/*.wav; do ffmpeg -i "${s}" -c:a flac "${s%.*}.flac"; rm "${s}"; done')

        

        return fetched_results
