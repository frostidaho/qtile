"""libqtile.images - create cairo surfaces from images

libqtile.images contains code to create and manipulate cairo surfaces and
objects from image files.

libqtile.images.Loader is intended as the primary tool in this module.
With Loader(...) you can load individual images (png or svg) by their path,
or load multiple icons with the Loader.icons method.
"""
import io
import cairocffi
import os
import re
from collections import namedtuple, defaultdict

from .log_utils import logger


class CairoImageSurface(object):
    """CairoImageSurface is a namespace for functions which convert images to cairo surfs

    Each image type has a classmethod or staticmethod named from_XYZ
    with a signature compatible with from_XYZ(bytes_string, **kwargs)
    e.g., from_png(...) and from_svg(...)

    Get a dictionary of available backends from:
    >>> d_backends = CairoImageSurface.get_backends()
    """
    @staticmethod
    def from_png(bytes_png, **kwargs):
        "from_png converts the data from a png file to a cairo ImageSurface."
        return cairocffi.ImageSurface.create_from_png(io.BytesIO(bytes_png))

    try:
        cairosvg = __import__('cairosvg')

        @classmethod
        def from_svg(cls, bytes_svg, width=None, height=None, dpi=200, **kwargs):
            """from_svg converts the data from a svg file to a cairo ImageSurface.

            from_svg(...) depends on the cairosvg library.
            """
            svg = cls.cairosvg
            tree = svg.parser.Tree(bytestring=bytes_svg)
            png_surf_file = io.BytesIO()
            png_surf = svg.surface.PNGSurface(
                tree,
                png_surf_file,
                dpi=dpi,
                parent_width=width,
                parent_height=height,
            )
            png_surf.finish()
            png_surf_file.seek(0)
            return cls.from_png(png_surf_file.read())

    except ImportError:
        logger.warning("Can't import cairosvg! "
                       "CairoImageSurface.from_svg will not be available.")

    @classmethod
    def get_backends(cls):
        backends = (x for x in dir(cls) if x.startswith('from_'))
        return {re.split('^from_', x, maxsplit=1)[-1]: getattr(cls, x)
                for x in backends}


class BackendError(Exception):
    pass


def path_to_image_surface(path, **kwargs):
    """Return a cairocffi.ImageSurface corresponding to the image at path

    Args:
       path (str): the path of the image file

    Kwargs:
       All keyword arguments are passed directly to the appropriate backend
       in CairoImageSurface.

    Returns:
       cairocffi.ImageSurface

    The filetype suffix needs to be present in CairoImageSurface.get_backends() or a
    BackendError will be raised.
    """
    path_lower = path.lower()
    for itype, fn in CairoImageSurface.get_backends().items():
        if path_lower.endswith('.' + itype):
            break
    else:
        msg = 'No image backend found for {!r}'.format(path)
        logger.warning(msg)
        raise BackendError(msg)
    with open(path, mode='rb') as fimg:
        return fn(fimg.read(), **kwargs)


def get_matching_files(dirpath, names, explicit_filetype=False):
    """Search dirpath recursively for files matching the names

    Return a dict with keys equal to entries in names
    and values a list of matching paths.
    """
    def match_files_in_dir(dirpath, regex_pattern):
        for dpath, dnames, fnames in os.walk(dirpath):
            matches = (regex_pattern.match(x) for x in fnames)
            for match in (x for x in matches if x):
                d = match.groupdict()
                d['directory'] = dpath
                yield d

    names = tuple(names)
    pat_str = '(?P<name>' + '|'.join(map(re.escape, names)) + ')'
    if explicit_filetype:
        pat_str += '$'
    else:
        pat_str += '\\.(?P<suffix>\w+)$'
    regex_pattern = re.compile(pat_str, flags=re.IGNORECASE)

    d_total = defaultdict(list)
    for d_match in match_files_in_dir(dirpath, regex_pattern):
        name, directory = d_match['name'], d_match['directory']
        try:
            suffix = d_match['suffix']
            filename = '.'.join((name, suffix))
        except KeyError:
            filename = name
        d_total[name].append(os.path.join(directory, filename))
    return d_total

LoadedImg = namedtuple('LoadedImg', 'success name path surface pattern width height')


class Loader(object):
    """Loader - create cairo surfaces from image files & icons

    load an image directly with Loader.__call__(). e.g.,
    >>> ldr = Loader()
    >>> loaded_image = ldr('/tmp/someimage.png')

    load icons using Loader.icons(). e.g.,
    >>> ldr = Loader(['/usr/share/icons/Adwaita/24x24', '/usr/share/icons/Adwaita'])
    >>> loaded_images = ldr.icons(['audio-volume-muted', 'audio-volume-low'])
    """

    def __init__(self, icon_dirs=(), width=None, height=None):
        """Create an instance of Loader

        Args:
           icon_dirs (:obj:`list` of :obj:`str`, optional):  Search for icons
               in these directories.
           width (int, optional): The width of the loaded image surface in pixels.
           height (int, optional): The height of the loaded image surface in pixels.

        icon_dirs is only used with Loader.icons
        """
        if not icon_dirs:
            self.icon_dirs = []
        else:
            self.icon_dirs = icon_dirs
        self.backends = CairoImageSurface.get_backends()
        self.width = width
        self.height = height

    def __call__(self, image_path, width=None, height=None, name=None):
        width = width if width is not None else self.width
        height = height if height is not None else self.height

        total = []
        if not image_path:
            logger.warning("Can't load image with no given path, name=%r", name)
            return LoadedImg(
                success=False,
                name=name,
                path=image_path,
                surface=None,
                pattern=None,
                width=None,
                height=None,
            )
            # return LoadedImg(False, name, image_path, None, None, None, None)

        if name is None:
            name = os.path.basename(image_path)
            name = re.split('\\.\w+$', name, maxsplit=1)[0]

        try:
            success, surface = True, path_to_image_surface(
                image_path,
                width=width,
                height=height,
            )
        except BackendError:
            logger.warning(
                "Can't load image with current backends, path=%r, name=%r",
                image_path,
                name,
            )
            success, surface = False, None
        except (OSError, IOError):
            logger.warning("Couldn't open image at path=%r, name=%r", image_path, name)
            success, surface = False, None
        pattern = self._get_pattern(surface, width, height)
        width, height = self._get_new_width_height(surface, width, height)
        return LoadedImg(
            success=success,
            name=name,
            path=image_path,
            surface=surface,
            pattern=pattern,
            width=width,
            height=height,
        )

    @staticmethod
    def _get_new_width_height(surface, width, height):
        if surface is None:
            return (None, None)
        if width is None:
            width = surface.get_width()
        if height is None:
            height = surface.get_height()
        return (width, height)

    @staticmethod
    def _get_pattern(surface, width, height):
        """Return a SurfacePattern from an ImageSurface.

        if width and height are not None scale the pattern
        to be size width and height.
        """
        if surface is None:
            return None
        pattern = cairocffi.SurfacePattern(surface)
        pattern.set_filter(cairocffi.FILTER_BEST)

        def scale(original, new):
            return float(original) / float(new)

        tr_width, tr_height = None, None
        if (width is not None) and (width != surface.get_width()):
            tr_width = scale(surface.get_width(), width)
        if (height is not None) and (height != surface.get_height()):
            tr_height = scale(surface.get_height(), height)
        if (tr_width is not None) or (tr_height is not None):
            tr_width = tr_width if tr_width is not None else 1.0
            tr_height = tr_height if tr_height is not None else 1.0
            matrix = cairocffi.Matrix()
            matrix.scale(tr_width, tr_height)
            pattern.set_matrix(matrix)
        return pattern

    def paths(self, image_paths, width=None, height=None):
        """paths() loads all of the images given in image_paths

        image_paths is an iterable of paths to image files
        paths() returns a list of loaded images: [LoadedImg(...), ...]
        """
        return [self(x, width=width, height=height) for x in image_paths]

    def icons(self, icon_names, width=None, height=None):
        """icons() loads all of the images given in icon_names

        icon_names is an iterable of icon names
        icons() returns a list of loaded images: [LoadedImg(...), ...]
        """
        names = tuple(icon_names)
        mfiles = get_matching_files(self.icon_dirs[0], names, explicit_filetype=False)
        for dpath in self.icon_dirs[1:]:
            mfiles2 = get_matching_files(dpath, names, explicit_filetype=False)
            for k, v in mfiles2.items():
                mfiles[k].extend(v)
        total = []
        for name in names:
            try:
                path = next(self._filter_paths(mfiles[name]))
            except StopIteration:
                path = None
            total.append(self(path, width=width, height=height, name=name))
        return total

    def _filter_paths(self, paths):
        pat = '\\.(' + '|'.join(self.backends) + ')$'
        pat = re.compile(pat, flags=re.IGNORECASE)
        for path in paths:
            if pat.search(path):
                yield path
            else:
                logger.info('No backend found for %r', path)
