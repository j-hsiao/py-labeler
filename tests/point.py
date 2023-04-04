from jhsiao.labeleritems import point, bindings, BGImage
from jhsiao.labeler import tk


def test_point():
    r = tk.Tk()
    c = tk.Canvas(r)
    c.grid()
    bindings.apply(c)
    im = BGImage(c)
    im.show(c, None)
    def onclick(e):
        pt = point.Point(e.widget, e.x, e.y, 'blue')
        pt.marktop(e.widget)
    c.tag_bind(im.idn, '<Button-1>', onclick)
    def check_cur(e):
        print('current Obj:', getattr(e.widget, 'objid', None))

    def getitems(e):
        print(point.Point.tops(e.widget))
        tops = set([
            point.Point.topid(e.widget, idn)
            for idn in e.widget.find('withtag', 'Obj')
        ])
        print(tops)
        for idn in tops:
            cls, idn = point.Point.parsetag(
                point.Point.toptag(e.widget, idn))
            print(cls, idn==idn)

    c.bind('<Button-1>', check_cur)
    c.bind('<Button-3>', getitems)

    r.bind('<q>', r.register(r.destroy))
    r.mainloop()
