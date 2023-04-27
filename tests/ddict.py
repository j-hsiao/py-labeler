from jhsiao.labeler.ddict import DDict

def test_ddict():
    d1 = dict(a=1, b=2, c=3)
    d2 = dict(b=3, c=4, d=5)
    od1 = d1.copy()
    od2 = d2.copy()

    d = DDict(d1, d2)
    d[69] = 42
    d['a'] = 0

    assert d['a'] == 0
    assert d['b'] == 2
    assert d['c'] == 3
    assert d['d'] == 5
    assert d[69] == 42
    assert d1 == od1
    assert d2 == od2

    assert dict(d.items()) == {'a':0, 'b':2, 'c':3, 69:42, 'd':5}
