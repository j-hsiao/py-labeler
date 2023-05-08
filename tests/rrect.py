from jhsiao.labeler import bindings
from jhsiao.labeler.canvas import LCanv
from jhsiao.labeler.objs import Crosshairs
from jhsiao.labeler.objs.rrect import RRect
from jhsiao.tkutil import tk

class Dummy(tk.Tk, object):
    def __init__(self, *args, **kwargs):
        super(Dummy, self).__init__(*args, **kwargs)
        self.objid = None
    def set_obj(self, idn):
        self.objid = idn

def test_rrect():
    r = tk.Tk()
    c = LCanv(r)
    c.grid()
    rect = RRect(c.canv, 50, 50, 'blue')
    print(c.canv.tag_bind('RRectVSide', '<Shift-Motion>'))
    print(rect.ids)
    for idn in rect.ids:
        print(idn, c.canv.gettags(idn))
    r.bind('<Escape>', r.register(r.destroy))
    bindings.apply(r)
    r.mainloop()
