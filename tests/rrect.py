from jhsiao.labeler import bindings as wbinds
from jhsiao.labeler.canvas import LCanv
from jhsiao.labeleritems import bindings, Crosshairs
from jhsiao.labeleritems.rrect import RRect
from jhsiao.tkutil import tk

def test_rrect():
    r = tk.Tk()
    wbinds.apply(r)
    c = LCanv(r)
    c.grid()
    rect = RRect(c.canv, 50, 50, 'blue')
    print(c.canv.tag_bind('RRectVSide', '<Shift-Motion>'))
    print(rect.ids)
    for idn in rect.ids:
        print(idn, c.canv.gettags(idn))
    r.bind('<Escape>', r.register(r.destroy))
    r.mainloop()
