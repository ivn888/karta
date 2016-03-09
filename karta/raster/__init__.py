"""
Classes for handling raster data.
"""

from . import grid
from . import misc

from .grid import RegularGrid, WarpedGrid, merge, gridpoints, hillshade, mask_poly
from .read import read_aai, read_gtiff, aairead, gtiffread
from .misc import witch_of_agnesi, peaks, pad, slope, aspect, grad, div
from .misc import normed_vector_field
from .crfuncs import streamline2d

__all__ = ["grid", "misc",
           "RegularGrid", "WarpedGrid",
           "aairead", "gtiffread", "read_aai", "read_gtiff",
           "pad", "slope", "aspect", "grad", "div", "normed_vector_field",
           "streamline2d"]

