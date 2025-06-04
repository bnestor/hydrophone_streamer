"""
hydrophone_streamer/src/supported_classes/base_class.py


"""


import time
from datetime import datetime
import glob
import os


class BaseStreamingClass:
    def __init__(self,
                 hydrophone_identifier: dict,
                 save_dir: str = 'data',
                 ) -> None:
        
        """
        """
        pass      

    def latest_file(self) -> None:
        """
        log the most recent audio file to a file for streaming purposes
        """  
        raise NotImplementedError("This method should be implemented in the subclass.")
    
    def download_data(self) -> list:
        """
        Download data from the hydrophone source.
        This method should be implemented in the subclass.
        """
        raise NotImplementedError("This method should be implemented in the subclass.")
        
    def stream_data(self) -> None:
        """
        
        """
        while True:

            fetched_results = self.download_data()
            


            print(f'fetched as recent as {datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}')

            if len(fetched_results) == 0:
                time.sleep(10)
            else:
                self.latest_file()


    def clean_old_files(self) -> None:
        """
        Clean old files in the save directory.
        """
        clean_old_files = glob.glob(os.path.join(self.save_dir, '*.flac'))
        clean_old_filed = clean_old_files + glob.glob(os.path.join(self.save_dir, '*.ts'))
        for file in clean_old_files:
            if os.path.getmtime(file) < time.time() - 60 * 60 * 24 * 7:
                # if file is older than 7 days
                os.remove(file)

            


            