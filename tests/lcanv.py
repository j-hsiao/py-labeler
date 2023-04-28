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
    r.bind('<Escape>', r.register(r.destroy))

    im = os.environ.get('IM')
    if im:
        lc.show(im)

    bindings.apply(r)
    r.mainloop()
