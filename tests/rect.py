from jhsiao.labeler import bindings
from jhsiao.labeler.objs.rect import Rect, RectPt
from jhsiao.tkutil import tk

def test_rect():
    r = tk.Tk()
    c = tk.Canvas(r)
    bindings.apply(c)
    c.grid()
    rect = Rect(c, 50, 50, 'blue')
    print(rect.ids)
    for idn in rect.ids:
        print(idn, c.gettags(idn))

    r.bind('<Escape>', r.register(r.destroy))

    def check(e):
        print(rect.data(c, rect.ids[0]))
        for idn in rect.ids[:5]:
            print(c.coords(idn))
        for idn in rect.ids[5:]:
            print(RectPt.data(c, idn))
    r.bind('<question>', check)
    r.mainloop()
