# -*- coding: utf-8 -*-

def convert_bytes(n: float) -> str:
    """ Converts a value expressed in bytes to a human readable String.

    :param n: Size in bytes.
    :returns: A string formatted in human readable format.
    :rtype: str.
    """
    K, M, G, T, P = 1 << 10, 1 << 20, 1 << 30, 1 << 40, 1 << 50
    if   n >= P:
        return "%.2fPb" % (float(n) / T)
    elif   n >= T:
        return "%.2fTb" % (float(n) / T)
    elif n >= G:
        return "%.2fGb" % (float(n) / G)
    elif n >= M:
        return "%.2fMb" % (float(n) / M)
    elif n >= K:
        return "%.2fKb" % (float(n) / K)
    else:
        return "%d" % n
