from __future__ import division
import cairocffi
import cairocffi.pixbuf
import io
import os
from collections import namedtuple

class LoadingError(Exception):
    pass

def _decode_to_image_surface(bytes_img, width=None, height=None):
    try:
        surf, fmt = cairocffi.pixbuf.decode_to_image_surface(bytes_img, width, height)
        return _SurfaceInfo(surf, fmt)
    except TypeError:
        from .log_utils import logger
        logger.exception("Couldn't set cairo image surface width and height")
        # need to use cairocffi patch to set width and height
        # https://github.com/frostidaho/cairocffi/tree/pixbuf_size
        surf, fmt = cairocffi.pixbuf.decode_to_image_surface(bytes_img)
        return _SurfaceInfo(surf, fmt)

_SurfaceInfo = namedtuple('_SurfaceInfo', ('surface', 'file_type'))
def get_cairo_surface(bytes_img, width=None, height=None):
    try:
        surf = cairocffi.ImageSurface.create_from_png(io.BytesIO(bytes_img))
        return _SurfaceInfo(surf, 'png')
    except (MemoryError, OSError):
        pass
    try:
        surf, fmt = _decode_to_image_surface(bytes_img, width, height)
        return _SurfaceInfo(surf, fmt)
    except cairocffi.pixbuf.ImageLoadingError:
        pass
    raise LoadingError("Couldn't load image!")

def get_cairo_pattern(surface, width, height, theta=0.0):
    """Return a SurfacePattern from an ImageSurface.

    if width and height are not None scale the pattern
    to be size width and height.

    theta is in degrees ccw
    """
    EPSILON = 1.0e-6
    from math import pi

    if surface is None:
        return None
    pattern = cairocffi.SurfacePattern(surface)
    pattern.set_filter(cairocffi.FILTER_BEST)
    matrix = cairocffi.Matrix()
    # TODO cleanup this function
    tr_width, tr_height = None, None
    if (width is not None) and (width != surface.get_width()):
        tr_width = surface.get_width() / width
    if (height is not None) and (height != surface.get_height()):
        tr_height = surface.get_height() / height
    if (tr_width is not None) or (tr_height is not None):
        tr_width = tr_width if tr_width is not None else 1.0
        tr_height = tr_height if tr_height is not None else 1.0
        matrix.scale(tr_width, tr_height)

    if abs(theta) > EPSILON:
        theta_rad = pi / 180.0 * theta
        mat_rot = cairocffi.Matrix.init_rotate(-theta_rad)
        matrix = mat_rot.multiply(matrix)

    pattern.set_matrix(matrix)
    return pattern

class _Descriptor(object):
    def __init__(self, name=None, default=None, **opts):
        self.name = name
        self.under_name = '_' + name
        self.default = default
        for key, value in opts.items():
            setattr(self, key, value)

    def __get__(self, obj, cls):
        if obj is None:
            return self
        _getattr = getattr
        try:
            return _getattr(obj, self.under_name)
        except AttributeError:
            return self.get_default(obj)

    def get_default(self, obj):
        return self.default

    def __set__(self, obj, value):
        setattr(obj, self.under_name, value)

    def __delete__(self, obj):
        delattr(obj, self.under_name)

class _Resetter(_Descriptor):
    def __set__(self, obj, value):
        super(_Resetter, self).__set__(obj, value)
        obj._reset()

class _PixelSize(_Resetter):
    def __set__(self, obj, value):
        value = max(int(value), 1)
        super(_PixelSize, self).__set__(obj, value)

class _Rotation(_Resetter):
    def __set__(self, obj, value):
        value = float(value)
        super(_Rotation, self).__set__(obj, value)

# class _Resettable(_Descriptor):
#     def __set__(self, obj, value):
#         msg = "{} can't be set".format(self.name)
#         raise TypeError(msg)

_ImgSize = namedtuple('_ImgSize', ('width', 'height'))


class Img(object):
    """Img is a class which creates & manipulates cairo SurfacePatterns from an image

    There are two constructors Img(...) and Img.from_path(...)

    The cairo surface pattern is at img.pattern.
    Changing any of the attributes width, height, or theta will update the pattern.

    - width :: pattern width in pixels
    - height :: pattern height in pixels
    - theta :: rotation of pattern counter clockwise in degrees
    Pattern is first stretched, then rotated.
    """
    def __init__(self, bytes_img, name='', path=''):
        self.bytes_img = bytes_img
        self.name = name
        self.path = path

    def _reset(self):
        attrs = ('surface', 'pattern')
        for attr in attrs:
            try:
                delattr(self, attr)
            except AttributeError:
                pass

    @classmethod
    def from_path(cls, image_path):
        "Create an Img instance from image_path"
        with open(image_path, 'rb') as fobj:
            bytes_img = fobj.read()
        name = os.path.basename(image_path)
        name, file_type = os.path.splitext(name)
        # file_type = file_type.lstrip('.')
        return cls(bytes_img, name=name, path=image_path)

    @property
    def default_surface(self):
        try:
            return self._default_surface
        except AttributeError:
            surf, fmt = get_cairo_surface(self.bytes_img)
            self._default_surface = surf
            return surf

    @property
    def default_size(self):
        try:
            return self._default_size
        except AttributeError:
            surf = self.default_surface
            size = _ImgSize(surf.get_width(), surf.get_height())
            self._default_size = size
            return size

    theta = _Rotation('theta', default=0.0)
    width = _PixelSize('width')
    height = _PixelSize('height')

    def scale(self, width_factor=None, height_factor=None, lock_aspect_ratio=False):
        if lock_aspect_ratio:
            res = self._scale_lock(width_factor, height_factor, self.default_size)
        else:
            res = self._scale_free(width_factor, height_factor, self.default_size)
        self.width, self.height = res

    @staticmethod
    def _scale_lock(width_factor, height_factor, initial_size):
        if width_factor and height_factor:
            raise ValueError(
                "Can't rescale with locked aspect ratio "
                "and give width_factor and height_factor."
                " {}, {}".format(width_factor, height_factor)
            )
        if not (width_factor or height_factor):
            raise ValueError('You must supply width_factor or height_factor')
        width0, height0 = initial_size
        if width_factor:
            width = width0 * width_factor
            height = height0 / width0 * width
        else:
            height = height0 * height_factor
            width = width0 / height0 * height
        return _ImgSize(width, height)

    @staticmethod
    def _scale_free(width_factor, height_factor, initial_size):
        if not (width_factor and height_factor):
            raise ValueError('You must supply width_factor and height_factor')
        width0, height0 = initial_size
        return _ImgSize(width0 * width_factor, height0 * height_factor)

    @property
    def surface(self):
        try:
            return self._surface
        except AttributeError:
            surf, fmt = get_cairo_surface(self.bytes_img, self.width, self.height)
            self._surface = surf
            return surf

    @surface.deleter
    def surface(self):
        try:
            del self._surface
        except AttributeError:
            pass


    @property
    def pattern(self):
        try:
            return self._pattern
        except AttributeError:
            pat = get_cairo_pattern(self.surface, self.width, self.height, self.theta)
            self._pattern = pat
            return pat

    @pattern.deleter
    def pattern(self):
        try:
            del self._pattern
        except AttributeError:
            pass

    def __repr__(self):
        return '<{cls_name}: {name!r}, {width}x{height}@{theta:.1f}deg, {path!r}>'.format(
            cls_name=self.__class__.__name__,
            name=self.name,
            width=self.width,
            height=self.height,
            path=self.path,
            theta=self.theta,
        )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        s0 = (self.bytes_img, self.theta, self.width, self.height)
        s1 = (other.bytes_img, other.theta, other.width, other.height)
        return s0 == s1
