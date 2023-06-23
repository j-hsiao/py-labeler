"""A namespace package for adding items for the labeler to use."""
__all__ = ['bindings', 'BGImage', 'Crosshairs', 'Obj']
from .. import bindings
from .obj import Obj
from .bgimage import BGImage
from .crosshairs import Crosshairs
from .point import Point
from .rect import Rect
from .rrect import RRect
