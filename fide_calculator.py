def fide_calculator(diff):
    szorzo = True
    if diff < 0:
        szorzo = False
        diff *= -1
    result = 0

    if diff <= 3: result = 0.5
    elif diff <= 10: result = 0.51
    elif diff <= 17: result = 0.52
    elif diff <= 25: result = 0.53
    elif diff <= 32: result = 0.54
    elif diff <= 39: result = 0.55
    elif diff <= 46: result = 0.56
    elif diff <= 53: result = 0.57
    elif diff <= 61: result = 0.58
    elif diff <= 68: result = 0.59
    elif diff <= 76: result = 0.6
    elif diff <= 83: result = 0.61
    elif diff <= 91: result = 0.62
    elif diff <= 98: result = 0.63
    elif diff <= 106: result = 0.64
    elif diff <= 113: result = 0.65
    elif diff <= 121: result = 0.66
    elif diff <= 129: result = 0.67
    elif diff <= 137: result = 0.68
    elif diff <= 145: result = 0.69
    elif diff <= 153: result = 0.7
    elif diff <= 162: result = 0.71
    elif diff <= 170: result = 0.72
    elif diff <= 179: result = 0.73
    elif diff <= 188: result = 0.74
    elif diff <= 197: result = 0.75
    elif diff <= 206: result = 0.76
    elif diff <= 215: result = 0.77
    elif diff <= 225: result = 0.78
    elif diff <= 235: result = 0.79
    elif diff <= 245: result = 0.8
    elif diff <= 256: result = 0.81
    elif diff <= 267: result = 0.82
    elif diff <= 278: result = 0.83
    elif diff <= 290: result = 0.84
    elif diff <= 302: result = 0.85
    elif diff <= 315: result = 0.86
    elif diff <= 328: result = 0.87
    elif diff <= 344: result = 0.88
    elif diff <= 357: result = 0.89
    elif diff <= 374: result = 0.9
    elif diff <= 391: result = 0.91
    elif diff <= 411: result = 0.92
    elif diff <= 432: result = 0.93
    elif diff <= 456: result = 0.94
    elif diff <= 484: result = 0.95
    elif diff <= 517: result = 0.96
    elif diff <= 559: result = 0.97
    elif diff <= 619: result = 0.98
    elif diff <= 735: result = 0.99
    else: result = 1

    return (result if szorzo else (1 - result))
	 	 