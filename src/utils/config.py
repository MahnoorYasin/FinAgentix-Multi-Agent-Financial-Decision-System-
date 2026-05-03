import yaml
from pathlib import Path

class Config:
    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def get(self, *keys):
        value = self.config
        for key in keys:
            value = value.get(key, {})
        return value
    
    def __getitem__(self, key):
        return self.config[key]

config = Config()