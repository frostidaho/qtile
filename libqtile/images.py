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
        backends =  (x for x in dir(cls) if x.startswith('from_'))
        return {re.split('^from_', x, maxsplit=1)[-1]:getattr(cls, x)
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


_MatchPath = namedtuple('_MatchPath', 'directory name suffix')
def get_matching_files(dirpath, *names):
    """Search dirpath recursively for files matching the names

    Return a dict with keys equal to entries in names
    and values a list of matching paths.
    """
    def _icons_iter(dirpath, *names):
        pat_str = '(?P<name>' + '|'.join(map(re.escape, names)) +')\\.(?P<suffix>\w+)$'
        pat = re.compile(pat_str)
        for dpath, dnames, fnames in os.walk(dirpath):
            matches = (pat.match(x) for x in fnames)
            matches = (x for x in matches if x)
            for match in matches:
                d = match.groupdict()
                yield _MatchPath(dpath, d['name'], d['suffix'])

    d = defaultdict(list)
    icons = _icons_iter(dirpath, *names)
    for directory, name, suffix in icons:
        d[name].append(os.path.join(directory, name+'.'+suffix))
    return d


LoadedImg = namedtuple('LoadedImg', 'success name path surface')
class Loader(object):
    """Loader - create cairo surfaces from image files & icons

    load an image directly with Loader.__call__(). e.g.,
    >>> ldr = Loader()
    >>> loaded_image = ldr('/tmp/someimage.png')

    load icons using Loader.icons(). e.g.,
    >>> ldr = Loader(['/usr/share/icons/Adwaita/24x24', '/usr/share/icons/Adwaita'])
    >>> loaded_images = ldr.icons('audio-volume-muted', 'audio-volume-low')
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

    def __call__(self, path, name=None):
        total = []
        if not path:
            logger.warning("Can't load image with no given path, name=%r", name)
            return LoadedImg(False, name, path, None)

        if name is None:
            name = os.path.basename(path)
            name = re.split('\\.\w+$', name, maxsplit=1)[0]

        try:
            success, surface = True, path_to_image_surface(
                path,
                width=self.width,
                height=self.height,
            )
        except BackendError:
            logger.warning("Can't load image with current backends, path=%r, name=%r", path, name)
            success, surface = False, None
        except (OSError, IOError):
            logger.warning("Couldn't open image at path=%r, name=%r", path, name)
            success, surface = False, None
        return LoadedImg(success, name, path, surface)

    def icons(self, *names):
        mfiles = get_matching_files(self.icon_dirs[0], *names)
        for dpath in self.icon_dirs[1:]:
            mfiles2 = get_matching_files(dpath, *names)
            for k,v in mfiles2.items():
                mfiles[k].extend(v)
        total = []
        for name in names:
            try:
                path = next(self._filter_paths(mfiles[name]))
            except StopIteration:
                path = None
            total.append(self(path, name=name))
        return total

    def _filter_paths(self, paths):
        pat = '\\.(' + '|'.join(self.backends) + ')$'
        pat = re.compile(pat, flags=re.IGNORECASE)
        for path in paths:
            if pat.search(path):
                yield path
            else:
                logger.info('No backend found for %r', path)

