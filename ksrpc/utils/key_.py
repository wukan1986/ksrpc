import hashlib
import pickle


# def make_key(module, name, args, kwargs, ref_id):
#     """生成缓存key
#
#     object部分由于repr后的id不同，导致字符串是不稳定的，不能作为key
#     """
#     key = f'{module}::{name}_{repr(args)}_{repr(kwargs)}_{ref_id}'
#     return hashlib.md5(key.encode('utf-8')).hexdigest()


def make_key(module, name, args, kwargs, ref_id):
    """生成缓存key。这种输出是否稳定还需考证"""
    d = dict(module=module, name=name, args=args, kwargs=kwargs, ref_id=ref_id)
    return hashlib.md5(pickle.dumps(d)).hexdigest()
