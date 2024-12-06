import json
import os

def load_config(config_file="config/config.json"):
    """ Load configuration from a JSON file """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file {config_file} not found.")

    with open(config_file, 'r') as f:
        config = json.load(f)
    
    return config

# Load configuration and print it
config = load_config()
