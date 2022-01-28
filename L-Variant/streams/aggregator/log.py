import logging.config
import yaml
import os

cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'logging.yml')

if os.path.isfile(cfg_path):
    with open(cfg_path, 'r') as f:
        log_cfg = yaml.safe_load(f.read())
    logging.config.dictConfig(log_cfg)
