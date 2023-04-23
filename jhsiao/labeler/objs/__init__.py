"""A namespace package for adding items for the labeler to use."""
__all__ = ['ibinds', 'BGImage']
from .. import bindings
ibinds = bindings('tag_bind')
from .obj import Obj
from .bgimage import BGImage
from .selector import ObjSelector
from .crosshairs import Crosshairs
