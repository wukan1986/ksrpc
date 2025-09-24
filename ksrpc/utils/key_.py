import hashlib


def make_key(module, name, args, kwargs):
    """生成缓存key"""
    key = f'{module}::{name}_{repr(args)}_{repr(kwargs)}'
    return hashlib.md5(key.encode('utf-8')).hexdigest()
