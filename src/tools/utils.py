from main.db import execute_query, get_connection
import re


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
        str = str.replace(',', '')

    return int(float(str) * multiplier)


def get_stats(stats_grp, stat_pos):
    subset = stats_grp[stat_pos].select('span span')
    return str(0) if not bool(subset[0].select('span')) else subset[0].select('span')[0].text