"""
cli.py
"""


import hydra
from omegaconf import DictConfig
from dotenv import load_dotenv, set_key
import os


from hydrophone_streamer.streamer import stream_data



# # Load .env file to get API token
# load_dotenv()
# token = os.getenv("ONC_TOKEN")

LOCAL_PATH = os.path.abspath(__file__)
print(LOCAL_PATH)
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(LOCAL_PATH)), 'hydrophone_streamer','configs')

print(CONFIG_PATH)


@hydra.main(config_path=CONFIG_PATH, config_name="config", version_base="1.3")
def main(cfg: DictConfig):
    
    
    stream_data(
        hydrophone_network=cfg.hydrophone_network,
        stream_setting=cfg.stream_setting,
        save_dir=cfg.save_dir,
    )

# Command to set the API token and store it in .env file
@hydra.main(config_path=CONFIG_PATH, config_name="token_config")
def set_token(cfg: DictConfig):
    # get project root directory
    dotenv_file = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)), '.env')

    set_key(dotenv_file, "ONC_TOKEN", cfg.ONC_token)
    print(f"ONC API token set successfully.")

if __name__ == "__main__":
    main()

