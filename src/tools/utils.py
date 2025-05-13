import argparse
from pathlib import Path
import json
import re

settings = {}


def parse_args():
    parser = argparse.ArgumentParser(description="Script with optional --setup flag")
    parser.add_argument('--setup', action='store_true', help='Run with database setup operations')
    parser.add_argument('--head', action='store_true', help='Run firefox in headed mode (visible)')
    return parser.parse_args()


def get_settings():
    global settings
    root_dir = Path(__file__).resolve().parent.parent.parent
    if len(settings) == 0:
        with open(f'{root_dir}/settings.json', 'r') as read_settings:
            for key, val in json.load(read_settings).items():
                settings[key] = val
    return settings


def str_to_int(str):
    multiplier = 1

    # Remove all whitespace (including non-breaking spaces)
    str = re.sub(r'\s+', '', str)

    # Determine if we need a multiplier nd clean the str
    if 'k' in str:
        multiplier = 1000
        str = str.replace('k', '')
    if 'M' in str:
        multiplier = 1000000
        str = str.replace('M', '')
    if ',' in str:
        str = str.replace(',', '.')

    return int(float(str) * multiplier)

