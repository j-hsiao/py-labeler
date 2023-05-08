from jhsiao.labeler import bindings
from jhsiao.tkutil import tk, add_bindtags
from jhsiao.labeler.objs import point


class dummy(tk.Tk, object):
    def __init__(self, *args, **kwargs):
        super(dummy, self).__init__(*args, **kwargs)
        self.objid = None

    def set_obj(self, idn):
        print('set_obj called')
        self.objid = idn

def test_point():
    r = dummy()
    r.grid_rowconfigure(0, weight=1)
    r.grid_columnconfigure(0, weight=1)
    c = tk.Canvas(r, background='green')
    c.grid(sticky='nsew')
    bindings.apply(c)
    def onclick(e):
        pt = point.Point(e.widget, e.x, e.y, 'blue')
        pt.marktop(e.widget)
    bgidn = c.create_rectangle(0, 0, 1000, 1000, fill='purple')
    c.addtag('BGImage', 'withtag', bgidn)
    c.tag_bind('BGImage', '<Button-1>', onclick)
    def check_cur(e):
        print('current Obj:', getattr(e.widget.master, 'objid', None))

    def getitems(e):
        print(point.Point.tops(e.widget))
        tops = set([
            point.Point.topid(e.widget, idn)
            for idn in e.widget.find('withtag', 'Obj')
        ])
        print(tops)
        for idn in tops:
            cls, oidn = point.Point.parsetag(
                point.Point.toptag(e.widget, idn))
            print(cls, idn==oidn)
            print(idn, e.widget.gettags(idn))

    c.bind('<Button-1>', check_cur)
    c.bind('<Button-3>', getitems)

    r.bind('<q>', r.register(r.destroy))
    r.mainloop()
