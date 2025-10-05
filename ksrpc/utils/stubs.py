"""
两个版本差异太大，为了能在python 3.6上使用，只能妥协
"""
from mypy.version import __version__

_v0 = int(__version__.strip('.')[0])
if _v0 == 0:
    from ksrpc.utils.stubs_0 import generate_stub  # noqa
else:
    from ksrpc.utils.stubs_1 import generate_stub  # noqa
