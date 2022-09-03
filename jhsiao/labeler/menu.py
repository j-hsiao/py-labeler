import sys
if sys.version_info.major > 2:
    import tkinter as tk
else:
    import Tkinter as tk

class Menu(tk.Menu, object):
    def __init__(self, master, items={}, *args, **kwargs):
        super(Menu, self).__init__(master, *args, **kwargs)
        for label, info in items.items():
            self._additem(label, **info)

    def _additem(self, label, **kwargs):
        tp = kwargs.pop('tp', 'command')
        if tp == 'cascade':
            menukwargs = kwargs.get('menu', {})
            menukwargs.setdefault('tearoff', False)
            submenu = Menu(self, **menukwargs)
            kwargs['menu'] = submenu
        getattr(self, 'add_'+tp)(label=label, **kwargs)



if __name__ == '__main__':
    from jhsiao import tkutil as tku
    def do_a(widget):
        print(repr(widget))
    def do_b(widget):
        print(repr(widget))

    r = tk.Tk()
    menu = Menu(
        r, dict(
            file=dict(
                tp='cascade',
                menu=dict(
                    items=dict(
                        a=dict(command=tku.EvSubs.make_script_(r, do_a, subs=dict(widget=(repr('hullo a'), str)))),
                        b=dict(command=tku.EvSubs.make_script_(r, do_b, subs=dict(widget=(repr('hello b'), str))))
                    )
                )),
            tools=dict(
                tp='cascade',
                menu=dict(
                    items=dict(
                        interpolate=dict(tp='command', command=' '))))))
    r.configure(menu=menu)
    r.bind('<Escape>', r.register(r.destroy))
    r.mainloop()
