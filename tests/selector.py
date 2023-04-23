from jhsiao.labeler.objs import ObjSelector
from jhsiao.tkutil import tk
from jhsiao.labeler import bindings


def test_selector():
    r = tk.Tk()
    bindings.apply(r)
    sel = ObjSelector(r)
    r.grid_rowconfigure(0, weight=1)
    r.grid_columnconfigure(0, weight=1)
    sel.grid(row=0, column=0, sticky='nsew')

    r.bind('<Return>', lambda e : print(sel()))

    r.bind('<Escape>', r.register(r.destroy))
    r.mainloop()
