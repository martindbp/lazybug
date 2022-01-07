import re
import hashlib
from typing import *
from time import time
from functools import wraps
from functools import partial


def md5sum_int64(string: str) -> int:
    d = hashlib.md5()
    d.update(string.encode('utf-8'))
    return int(d.hexdigest()[:4], 16)  # first 4 16-bit values is the first 64 bits


def file_md5sum(filename: str) -> str:
    with open(filename, mode='rb') as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()


def file_md5sum_int64(filename: str) -> int:
    with open(filename, mode='rb') as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
        return int(d.hexdigest()[:4], 16)  # first 4 16-bit values is the first 64 bits


def measure(func: Callable) -> Callable:
    @wraps(func)
    def _time_it(*args, **kwargs):
        start = int(round(time() * 1000))
        try:
            return func(*args, **kwargs)
        finally:
            end_ = int(round(time() * 1000)) - start
            print(f"Total execution time: {end_ if end_ > 0 else 0} ms")

    return _time_it


PUNCTUATION_REGEXP = '.*?([?\.,!？！，。]+)$'
def get_punctuation(from_str):
    matches = re.findall(PUNCTUATION_REGEXP, from_str)
    if len(matches) > 0:
        return matches[0]
    return None

def transfer_punctuation(from_str, to_str):
    from_str_punctuation = re.findall(PUNCTUATION_REGEXP, from_str)
    if len(from_str_punctuation) > 0:
        # If the caption text ends with a punctuation already, remove it
        to_str_punctuation = re.findall(PUNCTUATION_REGEXP, to_str)
        if len(to_str_punctuation) > 0:
            to_str = to_str[:-len(to_str_punctuation[0])]

        # Transfer the punctuation from the from_str to the to_str
        to_str += from_str[-len(from_str_punctuation[0]):]

    return to_str
