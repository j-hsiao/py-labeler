from jhsiao.labeler.objs import composite
from jhsiao.labeler.objs import rect, rrect, point
from jhsiao.labeler.canvas import LCanv
from jhsiao.labeler import bindings
from jhsiao.tkutil import tk

def test_composite():
    r = tk.Tk()
    bindings.apply(r)
    r.grid_rowconfigure(0, weight=1)
    r.grid_columnconfigure(0, weight=1)
    c = LCanv(r)
    c.grid(row=0, column=0, sticky='nsew')
    compositeclass = composite.make_composite(
        'tst', [rect.Rect, rrect.RRect, point.Point])
    compositeclass.register(compositeclass)
    compositeclass(c.canv, 50, 50, 'black')
    rrect.RRect(c.canv, 100, 50, 'blue')
    r.bind('<Escape>', r.register(r.destroy))
    r.mainloop()
