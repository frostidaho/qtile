import libqtile.images as images
import cairocffi
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(TEST_DIR, 'data')


############################################################
# Tests for images.path_to_image_surface
############################################################ 
def path_to_img_surf_equal(path):
    try:
        surf = images.path_to_image_surface(path)
        if isinstance(surf, cairocffi.ImageSurface):
            return True
    except images.BackendError:
        return True
    return False

def test_path_to_img_surf_png():
    path = os.path.join(DATA_DIR, 'png', 'audio-volume-muted.png')
    assert path_to_img_surf_equal(path)

def test_path_to_img_surf_svg():
    path = os.path.join(DATA_DIR, 'svg', 'audio-volume-muted.svg')
    assert path_to_img_surf_equal(path)

def test_path_to_img_surf_svg_size():
    path = os.path.join(DATA_DIR, 'svg', 'audio-volume-muted.svg')
    try:
        surf = images.path_to_image_surface(path)
        width, height = surf.get_width(), surf.get_height()
        assert (width, height) == (24, 24)

        surf = images.path_to_image_surface(path, width=80, height=16)
        width, height = surf.get_width(), surf.get_height()
        assert (width, height) == (80, 16)
    except images.BackendError:
        pass


############################################################ 
# tests for images.get_matching_files
############################################################ 
def test_get_matching_files():
    def name2path(name, suffix):
        return os.path.join(DATA_DIR, suffix, name + '.' + suffix)
    audio_name = 'audio-volume-muted'
    battery_name = 'battery-caution-charging'
    d = images.get_matching_files(
        DATA_DIR,
        (audio_name,
         battery_name),
    )
    audio_files = [
        name2path(audio_name, 'svg'),
        name2path(audio_name, 'png'),
    ]
    assert set(d[audio_name]) == set(audio_files)
    battery_files = [name2path(battery_name, 'png')]
    assert d[battery_name] == battery_files


def test_get_matching_files_explicit_filetype():
    audio_name = 'audio-volume-muted.png'
    d = images.get_matching_files(
        DATA_DIR,
        (audio_name,
         'battery-caution-charging.png',),
        explicit_filetype=True,
    )
    audio_files = [os.path.join(DATA_DIR, 'png', audio_name)]
    assert set(d[audio_name]) == set(audio_files)

def test_get_matching_files_explicit_fail():
    fname = 'audio-volume-muted.png'
    d = images.get_matching_files(
        os.path.join(DATA_DIR, 'svg'),
        (fname,),
        explicit_filetype=True,
    )
    assert d[fname] == []

def test_get_matching_files_explicit_mixed():
    fname = 'audio-volume-muted.png'
    fname2 = 'audio-volume-muted.svg'
    d = images.get_matching_files(
        os.path.join(DATA_DIR, 'svg'),
        (fname, fname2),
        explicit_filetype=True,
    )
    assert d[fname2] == [os.path.join(DATA_DIR, 'svg', fname2),]
    assert d[fname] == []


############################################################
# tests for images.Loader
############################################################ 
def loaded_img_eql(loaded_img, *args, **kwargs):
    for k,v in kwargs.items():
        assert getattr(loaded_img, k) == v
    for a,b in zip(loaded_img, args):
        assert a == b

def test_loader_empty():
    ldr = images.Loader()
    loaded_img_eql(ldr(''), path='', success=False, surface=None)
    loaded_img_eql(ldr(None), path=None, success=False, surface=None)

def test_loader_bad_filetype():
    ldr = images.Loader()
    name = 'somefile'
    path = '/a/b/{}.txt'.format(name)
    loaded_img_eql(ldr(path), path=path, success=False, surface=None, name=name)

def test_loader_file_not_exist():
    ldr = images.Loader()
    name = 'somefile'
    path = '/a/b/{}.png'.format(name)
    loaded_img_eql(
        ldr(path),
        path=path,
        success=False,
        surface=None,
        name=name,
        pattern=None,
    )

def test_loader_png():
    ldr = images.Loader()
    path = os.path.join(DATA_DIR, 'png', 'battery-caution-charging.png')
    loaded_img = ldr(path)
    loaded_img_eql(loaded_img, path=path, success=True, name='battery-caution-charging')
    surf = loaded_img.surface
    assert isinstance(surf, cairocffi.ImageSurface)
    pattern = loaded_img.pattern
    assert isinstance(pattern, cairocffi.SurfacePattern)


def test_loader_icon_png_exist():
    icon_dir = os.path.join(DATA_DIR, 'png')
    ldr = images.Loader([icon_dir,])

    loaded_imgs = ldr.icons(['audio-volume-muted',])
    loaded_img = loaded_imgs[0]
    loaded_img_eql(
        loaded_img,
        name='audio-volume-muted',
        success=True,
    )

def test_loader_icon_png_multiple():
    icon_dir = os.path.join(DATA_DIR, 'png')
    ldr = images.Loader([icon_dir,])
    names = ('battery-caution-charging', 'audio-volume-muted')

    loaded_imgs = ldr.icons(names)
    for i,name in enumerate(names):
        loaded_img = loaded_imgs[i]
        loaded_img_eql(
            loaded_img,
            name=name,
            success=True,
        )


def test_loader_icon_png_fail():
    icon_dir = os.path.join(DATA_DIR, 'png')
    ldr = images.Loader([icon_dir,])
    names = ('battery-caution-charging', 'audio-volume-nope')
    successful = (True, False)

    loaded_imgs = ldr.icons(names)
    for i,name in enumerate(names):
        loaded_img_eql(
            loaded_imgs[i],
            name=name,
            success=successful[i],
        )
