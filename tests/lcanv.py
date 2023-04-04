from jhsiao.tkutil import tk

from jhsiao.labeler.canvas import LCanv
from jhsiao.labeler import bindings

def test_lcanv():
    r = tk.Tk()
    bindings.apply(r)
    lc = LCanv(r)
    lc.grid()

    r.bind('<Escape>', r.register(r.destroy))
    r.mainloop()
