__all__ = ['Crosshairs']
import math

class Crosshairs(object):
    """Canvas crosshairs."""
    TAG = 'Crosshairs'
    UP = (0,1)
    def __init__(self, master):
        k = dict(
            state='disabled',
            tags=('Crosshairs',))
        # add thicker black to back for contrast.
        self.idns = (
            master.create_line(0, 0, 1, 1, fill='black', width=3, **k),
            master.create_line(0, 0, 1, 1, fill='black', width=3, **k),
            master.create_line(0, 0, 1, 1, fill='white', width=1, **k),
            master.create_line(0, 0, 1, 1, fill='white', width=1, **k))
        master.tag_raise('Crosshairs')
        master.configure(cursor='None')
        self._up = (0, 1)

    def up(self, x, y):
        if x or y:
            self._up = (x, y)
        else:
            self._up = (0,1)

    @staticmethod
    def hide(master):
        master.itemconfigure('Crosshairs', state='hidden')

    @staticmethod
    def show(master):
        master.itemconfigure('Crosshairs', state='disabled')

    @staticmethod
    def _edgepts(dx1, dx2, dy1, dy2, vx, vy, cx, cy):
        """Return vectors to reach the edges of the canvas.

        dx/dy: int
            Signed distance to an edge.
        vx, vy: vector direction.
        cx, cy: int
            canvas coordinates of mouse.
        """
        if vx:
            mx = (dx1 / vx, dx2 / vx)
            if mx[0] > mx[1]:
                mx = mx[::-1]
        else:
            mx = [-math.inf, math.inf]
        if vy :
            my = (dy1 / vy, dy2 / vy)
            if my[0] > my[1]:
                my = my[::-1]
        else:
            my = [-math.inf, math.inf]
        m1 = max(mx[0], my[0])
        m2 = min(mx[1], my[1])
        return (
            (int(vx*m1)+cx, int(vy*m1)+cy),
            (int(vx*m2)+cx, int(vy*m2)+cy))

    def moveto(self, master, x, y):
        """Place crosshairs at location.

        master: tk.Canvas
        x,y: int, the widget mouse x,y coords (not canvasxy)
        """
        w = master.winfo_width()
        h = master.winfo_height()
        cx = master.canvasx(x)
        cy = master.canvasy(y)
        vx, vy = self._up
        (x1,y1), (x2,y2) = self._edgepts(
            -x, w-x, -y, h-y, vx, vy, cx, cy)
        idns = self.idns
        master.coords(idns[0], x1, y1, x2, y2)
        master.coords(idns[2], x1, y1, x2, y2)
        (x1,y1), (x2,y2) = self._edgepts(
            -x, w-x, -y, h-y, vy, -vx, cx, cy)
        master.coords(idns[1], x1, y1, x2, y2)
        master.coords(idns[3], x1, y1, x2, y2)

