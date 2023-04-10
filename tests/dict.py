from jhsiao.labeler.dict import Dict
from jhsiao.labeler import bindings
from jhsiao.tkutil import tk


def test_dict():
    r = tk.Tk()
    bindings.apply(r)
    r.grid_columnconfigure(0, weight=1)
    r.grid_rowconfigure(0, weight=1)
    d = Dict(r)
    d.grid(row=0, column=0, sticky='nsew')

    def check():
        print(d.dict())
    b = tk.Button(r, text='check')
    b.grid(row=1, column=0, sticky='nsew')
    b.configure(command=check)
    r.bind('<Escape>', r.register(r.destroy))
    r.mainloop()
