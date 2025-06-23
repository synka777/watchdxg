from environs import Env
from pathlib import Path
import argparse
import json

env = Env()
env.read_env()


def parse_args():
    parser = argparse.ArgumentParser(description="Script with optional --setup flag")
    parser.add_argument('--setup', action='store_true', help='Run with database setup operations')
    parser.add_argument('--head', action='store_true', help='Run firefox in headed mode (visible)')
    parser.add_argument('--dev', action='store_true', help='Run in dev (local, non-virtualized) mode')
    return parser.parse_args()


def get_settings():
    settings = {}
    src_dir = Path(__file__).resolve().parent

    with open(f'{src_dir}/settings.json', 'r') as read_settings:
        for key, val in json.load(read_settings).items():
            settings[key] = val

    return settings


settings = get_settings()  # <-- settings is always ready when imported