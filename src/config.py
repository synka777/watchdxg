from environs import Env
from pathlib import Path
import json

env = Env()
env.read_env()

def get_settings():
    settings = {}
    root_dir = Path(__file__).resolve().parent.parent

    print(f'{root_dir}/settings.json')
    with open(f'{root_dir}/settings.json', 'r') as read_settings:
        for key, val in json.load(read_settings).items():
            settings[key] = val

    return settings

settings = get_settings()  # <-- settings is always ready when imported