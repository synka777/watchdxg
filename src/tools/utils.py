from main.db import execute_query, get_connection
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


def str_to_int(str):
    multiplier = 1

    # Remove all whitespace (including non-breaking spaces)
    str = re.sub(r'\s+', '', str)

    # Determine if we need a multiplier nd clean the str
    if 'k' in str:
        multiplier = 1000
        str = str.replace('k', '')
    if 'K' in str:
        multiplier = 1000
        str = str.replace('K', '')
    if 'M' in str:
        multiplier = 1000000
        str = str.replace('M', '')
    if ',' in str:
        str = str.replace(',', '.')

    return int(float(str) * multiplier)


def get_stats(stats_grp, stat_pos):
    subset = stats_grp[stat_pos].select('span span')
    return str(0) if not bool(subset[0].select('span')) else subset[0].select('span')[0].text


def clean_stat(stat):
    return stat.replace('0', '') if stat.startswith('0') else stat