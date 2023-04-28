class DDict(object):
    """Wrap dict."""
    def __init__(self, *dicts):
        self.baks = dicts
        self.main = {}

    def __getitem__(self, k):
        try:
            return self.main[k]
        except KeyError:
            for bak in self.baks:
                try:
                    return bak[k]
                except KeyError:
                    pass
        raise KeyError(repr(k))

    def __delitem__(self, k):
        del self.main[k]

    def __setitem__(self, k, v):
        if k == Ellipsis:
            self.main = v
        else:
            self.main[k] = v

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def __repr__(self):
        return '({},{})'.format(repr(self.main), repr(self.baks))

    def __len__(self):
        return len(list(self.keys()))

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def keys(self):
        for k in self.main:
            yield k
        s = set(self.main)
        for bak in self.baks:
            for k in bak:
                if k not in s:
                    s.add(k)
                    yield k

    def values(self):
        for k in self.keys():
            yield self[k]
    def items(self):
        for k in self.keys():
            yield k, self[k]
