from jhsiao.labeler.objs import Crosshairs
from jhsiao.tkutil import tk

def test_crosshairs():
    r = tk.Tk()
    c = tk.Canvas(r, highlightthickness=0, borderwidth=0)
    c.grid()
    x = Crosshairs(c)
    def movecursor(e):
        x.moveto(e.widget, e.x, e.y)

    def left(e):
        print('left')
        x.hide(e.widget)
    def entered(e):
        print('entered')
        c.focus_set()
        x.show(e.widget)
    org = []
    def anchor(e):
        print('anchor')
        org[:] = e.x, e.y
    def ranchor(e):
        print('ranchor')
        ax, ay = org
        x.up = e.x-ax, e.y-ay
        x.moveto(e.widget, e.x, e.y)
    def unanchor(e):
        print('unanchored')
        x.up = x.UP
        x.moveto(e.widget, e.x, e.y)
    c.bind('<Motion>', movecursor)
    c.bind('<Enter>', entered)
    c.bind('<Leave>', left)
    c.bind('<Button-1>', anchor)
    c.bind('<B1-Motion>', ranchor)
    c.bind('<ButtonRelease-1>', unanchor)
    c.bind('<h>', lambda e : x.hide(e.widget))
    c.bind('<s>', lambda e : x.show(e.widget))

    r.bind('<Escape>', r.register(r.destroy))
    r.mainloop()
