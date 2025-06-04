"""
streamer.py
"""

import os
import json


from hydrophone_streamer.supported_classes.ooi_streaming_class import OOIStreamingClass
from hydrophone_streamer.supported_classes.onc_streaming_class import ONCStreamingClass
# from supported_classes.orcasound_streaming_class import OrcasoundStreamingClass

from typing import Union

def stream_data(
        hydrophone_network: str,
        stream_setting : Union[str, dict],
        save_dir: str = 'data',
        
) -> None:
    """
    Stream data from a hydrophone based on its identifier.

    Args:
        hydrophone_identifier (Union[str, dict]): Identifier for the hydrophone.
            Can be a string or a dictionary with specific keys.

    Returns:
        None
    """
    
    if isinstance(stream_setting, str):
        print(stream_setting)
        assert os.path.exists(hydrophone_identifier), "hydrophone configuration file does not exist."
        with open(hydrophone_identifier, 'r') as file:
            hydrophone_identifier = json.load(file)
    
    if hydrophone_network == 'onc':
        streaming_class = ONCStreamingClass(stream_setting, save_dir=save_dir)
    elif hydrophone_network == 'ooi':
        # i.e. hydrophone-streamer save_dir=/home/user/Documents/ stream_setting="{'url':'https://rawdata-west.oceanobservatories.org/files/CE02SHBP/LJ01D/HYDBBA106/'}" hydrophone_network="ooi"
        streaming_class = OOIStreamingClass(stream_setting, save_dir=save_dir)
    elif hydrophone_network == 'orcasound':
        streaming_class = OrcasoundStreamingClass(stream_setting, save_dir=save_dir)
    else:
        raise ValueError(f"Unsupported network type: {hydrophone_network}")
    
    streaming_class.stream_data()