# -*- coding: utf-8 -*-
from config_loader import *
_mc = config.get_default_mc()


def auto_mc(func):
    """自动memcache装饰器
    """

    def _auto_mc(*args, **kwargs):
        key = func.func_name + '_' + '_'.join([str(item) for item in (list(args) + kwargs.values())])
        obj = _mc.get(key)
        if obj is None:
            obj = func(*args, **kwargs)
            _mc.set(key, obj)
        return obj
    return _auto_mc


@auto_mc
def test_auto_mc():
    return 5


if __name__ == '__main__':
    print test_auto_mc()    