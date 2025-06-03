from main.db import execute_query, get_connection
import argparse
import re

settings = {}


def filter_known(handles: list[str]):
    filtered = []
    for handle in handles:
        # Stop adding new handles to the processing list as soon as a handle
        # is found in database and return the result
        if execute_query(
                    get_connection(),
                    'SELECT * FROM users WHERE handle = %s',
                    params = (handle,),
                    fetchone = True
                ):
            return filtered
        else:
            filtered.append(handle)
    return filtered # filtered == handles at this point


def parse_args():
    parser = argparse.ArgumentParser(description="Script with optional --setup flag")
    parser.add_argument('--setup', action='store_true', help='Run with database setup operations')
    parser.add_argument('--head', action='store_true', help='Run firefox in headed mode (visible)')
    return parser.parse_args()


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

