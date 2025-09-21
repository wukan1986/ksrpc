import sys


def muted_print(*args, **kwargs):
    pass


def update_progress(i, print, file=sys.stderr):
    """简化版进度条"""
    j = i % 10
    if j == 0:
        print('0', end='', file=file)
    elif j == 9:
        print('\b=', end='', file=file)
    else:
        print(f'\b{j}', end='', file=file)
