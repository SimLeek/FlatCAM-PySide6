"""Paths and patches"""
import logging

from matplotlib.patches import PathPatch
from matplotlib.path import Path
from numpy import asarray, concatenate, ones

log = logging.getLogger('base')


class Polygon(object):
    """
    Adapts Shapely or GeoJSON (geo_interface) polygons to a common interface.
    Provides consistent access to `geom_type`, `exterior`, and `interiors` properties.
    """
    def __init__(self, context):
        # Check if context is a Shapely polygon
        if hasattr(context, 'interiors') or hasattr(context, 'exterior'):
            self._is_shapely = True
            self.context = context
        # Check if context has a GeoJSON-like __geo_interface__
        elif hasattr(context, '__geo_interface__'):
            self._is_shapely = False
            self.context = context.__geo_interface__
        # Assume it is a GeoJSON dictionary
        else:
            self._is_shapely = False
            self.context = context

    @property
    def geom_type(self):
        """
        Returns the geometry type as a string (e.g., 'Polygon').
        """
        if self._is_shapely:
            log.debug("returning shapely geom type")
            return self.context.geom_type
        return self.context.get('type', None)

    @property
    def exterior(self):
        """
        Returns the exterior boundary. For Shapely, this is an object with coordinates;
        for GeoJSON, it's a list of coordinate pairs.
        """
        if self._is_shapely:
            log.debug("returning shapely exterior")
            ext_list = list(self.context.exterior.coords)
            if len(ext_list)==0:
                return None
            return ext_list
        return self.context.get('coordinates', [])[0]

    @property
    def interiors(self):
        """
        Returns the interior boundaries (holes). For Shapely, this is a list of objects
        with coordinates; for GeoJSON, it's a list of lists of coordinate pairs.
        """
        if self._is_shapely:
            log.debug("returning shapely interiors")
            return [list(interior.coords) for interior in self.context.interiors]
        return self.context.get('coordinates', [])[1:]



def PolygonPath(polygon):
    """Constructs a compound matplotlib path from a Shapely or GeoJSON-like
    geometric object"""
    this = Polygon(polygon)
    assert this.geom_type == 'Polygon', f"Wrong Type: {this.geom_type}"
    log.debug(f"exterior: {this.exterior}")

    def coding(ob):
        # The codes will be all "LINETO" commands, except for "MOVETO"s at the
        # beginning of each subpath
        n = len(getattr(ob, 'coords', None) or ob)
        vals = ones(n, dtype=Path.code_type) * Path.LINETO
        vals[0] = Path.MOVETO
        return vals
    if this.exterior is None:
        return None
    #log.debug(f"exterior: {[asarray(this.exterior)]
    #                + [asarray(r) for r in this.interiors]}")
    vertices = concatenate(
                    [asarray(this.exterior)]
                    + [asarray(r) for r in this.interiors])
    codes = concatenate(
                [coding(this.exterior)]
                + [coding(r) for r in this.interiors])
    return Path(vertices, codes)


def PolygonPatch(polygon, **kwargs):
    """Constructs a matplotlib patch from a geometric object
    
    The `polygon` may be a Shapely or GeoJSON-like object with or without holes.
    The `kwargs` are those supported by the matplotlib.patches.Polygon class
    constructor. Returns an instance of matplotlib.patches.PathPatch.

    Example (using Shapely Point and a matplotlib axes):

      >>> b = Point(0, 0).buffer(1.0)
      >>> patch = PolygonPatch(b, fc='blue', ec='blue', alpha=0.5)
      >>> axis.add_patch(patch)

    """
    ppath = PolygonPath(polygon)
    if ppath is not None:
        p = PathPatch(ppath, **kwargs)
        return p
    else:
        return None
