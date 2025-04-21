
def str_to_int(str):
    multiplier = 1

    # Determine if we need a multiplier nd clean the str
    if 'k' in str:
        multiplier = 1000
        str = str.replace(' k', '')
    if 'M' in str:
        multiplier = 1000000
        str = str.replace(' M', '')

    if ',' not in str: # Replace comma with a dot for it to be convertible to a float
        str = str.replace(' ', '')
    else:
        str = str.replace(',', '.')
    return int(float(str) * multiplier)