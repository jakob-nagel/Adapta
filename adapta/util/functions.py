import numpy as np


def int_(num_bits):
    """Creates the numpy integer data type corresponding to the specified
    number of bits.

    Parameters
    ----------
    num_bits : int
        The number of bits the data type uses.

    Returns
    -------
    numpy dtype
        The numpy integer data type.

    """

    return np.dtype('int{}'.format(num_bits))


def round_(number):
    """Rounds the given number to an integer and makes sure that the result can
    be used for indexing lists.

    Parameters
    ----------
    number : float
        The number to be rounded.

    Returns
    -------
    int
        The rounded number.

    """

    return np.round(number).astype(np.int)


def intmax(dtype):
    """Fetches the maximum value the given numpy data type can have.

    Parameters
    ----------
    dtype : numpy dtype
        The numpy data type.

    Returns
    -------
    int
        The maximum value.

    """

    return np.iinfo(dtype).max


def db_to_ratio(db):
    """Converts the volume of an audio track to the ratio its samples need to
    be scaled with.

    Parameters
    ----------
    db : float
        The volumne in decibel.

    Returns
    -------
    float
        The corresponding ratio.

    """

    return 10 ** (db / 20)


def bpm_to_time(bpm):
    return 60 / bpm


def time_to_bpm(time):
    return 60 / time


def isarray(x):
    return all(hasattr(x, attr) for attr in ('__len__', '__getitem__'))


def expspace(x, y, exp, num):
    deltas = np.subtract(y, x)
    signs = np.sign(deltas)
    degrees = np.power(2.0, signs * exp)
    factors = np.divide(np.geomspace(1, degrees, num, False) - 1, degrees - 1,
                        where=degrees != 1)
    return np.add(factors * deltas,  x)


def seconds_to_time(seconds, digits=3):
    if seconds < 0:
        seconds = -seconds
        sign = '-'
    else:
        sign = ''
    minutes, seconds = divmod(seconds, 60)
    string = '{{}}{{:d}}:{{:0{}.{}f}}'.format(digits + 3, digits)
    return string.format(sign, int(minutes), seconds)


def time_to_seconds(time):
    split = time.split(':')
    if len(split) == 1:
        return float(time)
    minutes = int(split[0])
    seconds = float(split[1])
    return minutes * 60 + seconds


def load_beats(path):
    return np.loadtxt(path, converters={0: time_to_seconds}, usecols=0,
                      encoding='latin1')
