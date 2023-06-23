"""Layered dicts for default values.

Setting and deleting values only does so on the topmost DDict.
"""
import sys
if sys.version_info.major > 2:
    from collections.abc import MutableMapping
else:
    from collections import MutableMapping

class DDict(MutableMapping):
    """Access multiple dicts as a single dict.

    Modifications only affect the very first dict.
    """
    def __init__(self, *dicts):
        if not dicts:
            self.dicts = [{}]
        else:
            self.dicts = list(dicts)

    def __getitem__(self, k):
        """Return value from the first dict containing `k`.

        If None contain `k`, raise KeyError.
        """
        for d in self.dicts:
            try:
                return d[k]
            except KeyError:
                pass
        else:
            raise KeyError(repr(k))

    def __delitem__(self, k):
        """Remove a key from first dict if exists."""
        self.dicts[0].pop(k)

    def __setitem__(self, k, v):
        """Add a key to first dict."""
        self.dicts[0][k] = v

    def __repr__(self):
        return 'DDict{}'.format(self.dicts)

    def __len__(self):
        return len(list(self))

    def __iter__(self):
        covered = set()
        for d in self.dicts:
            for k in d:
                if k not in covered:
                    yield k
                    covered.add(k)

    def get(self, name, default=None):
        """Return value from dict or `default` if not found."""
        for d in self.dicts:
            try:
                return d[k]
            except KeyError:
                pass
        else:
            return default

    def pop(self, key, *default):
        """Remove and return a key from first dict.

        If first dict does not contain the key, then take
        values from following dicts.  If None, then return
        default value.

        If no default was given, then raise a KeyError if
        key not found in any dicts.
        In any case, the first dict will not have `key` as a key after
        this call.
        """
        thing = self.get(key, default)
        self.dicts[0].pop(key)
        if thing is default:
            if default:
                return default[0]
            else:
                raise KeyError(repr(key))
        else:
            return thing

    def update(self, *args, **kwargs):
        self.dicts[0].update(*args, **kwargs)

    def keys(self):
        return iter(self)

    def values(self):
        covered = set()
        for d in self.dicts:
            for k, v in d.items():
                if k not in covered:
                    yield v
                    covered.add(k)

    def items(self):
        covered = set()
        for d in self.dicts:
            for t in d.items():
                if t[0] not in covered:
                    yield t
                    covered.add(t[0])
