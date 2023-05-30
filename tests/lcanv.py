import os

from jhsiao.tkutil import tk
from jhsiao.labeler.canvas import LCanv
from jhsiao.labeler import bindings



def test_lcanv():
    r = tk.Tk()
    r.grid_rowconfigure(0, weight=1)
    r.grid_columnconfigure(0, weight=1)
    lc = LCanv(r, border=0, highlightthickness=0)
    lc.grid(sticky='nsew')
    r.bind('<Shift-Escape>', r.register(r.destroy))
    lc.canv.bind('<BackSpace>', lc.register(lc.clear))

    def check(e):
        print(lc.selector.classinfo)
        print('modified?', lc.modified())
    r.bind('<question>', check)
    def reset(e):
        print('reset')
        lc._changed = False
    r.bind('<slash>', reset)

    states = []

    def pushstate(e):
        data = lc.data()
        print(data)
        states.append(data)

    def popstate(e):
        if states:
            lc.restore(states.pop())

    def clear(e):
        lc.clear()

    lc.canv.bind('<Left>', pushstate)
    lc.canv.bind('<Right>', popstate)
    lc.canv.bind('<Down>', clear)

    im = os.environ.get('IM')
    if im:
        lc.show(im)

    bindings.apply(r)
    r.mainloop()
