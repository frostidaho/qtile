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

def loaded_img_eql(loaded_img, *args, **kwargs):
    for k,v in kwargs.items():
        assert getattr(loaded_img, k) == v
    for a,b in zip(loaded_img, args):
        assert a == b

############################################################ 
# tests for images.get_matching_files
############################################################ 
def test_get_matching_files():
    d = images.get_matching_files(
        DATA_DIR,
        'audio-volume-muted',
        'battery-caution-charging',
    )
    
    audio_files = [
        os.path.join(DATA_DIR, 'svg', 'audio-volume-muted.svg'),
        os.path.join(DATA_DIR, 'png', 'audio-volume-muted.png'),
    ]
    assert set(d['audio-volume-muted']) == set(audio_files)
    battery_files = [
        os.path.join(DATA_DIR, 'png', 'battery-caution-charging.png'),
    ]
    assert d['battery-caution-charging'] == battery_files


############################################################
# tests for images.Loader
############################################################ 
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
    loaded_img_eql(ldr(path), path=path, success=False, surface=None, name=name)

def test_loader_png():
    ldr = images.Loader()
    path = os.path.join(DATA_DIR, 'png', 'battery-caution-charging.png')
    loaded_img = ldr(path)
    loaded_img_eql(loaded_img, path=path, success=True, name='battery-caution-charging')
    surf = loaded_img.surface
    assert isinstance(surf, cairocffi.ImageSurface)


def test_loader_icon_png_exist():
    icon_dir = os.path.join(DATA_DIR, 'png')
    ldr = images.Loader([icon_dir,])

    loaded_imgs = ldr.icons('audio-volume-muted')
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

    loaded_imgs = ldr.icons(*names)
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

    loaded_imgs = ldr.icons(*names)
    for i,name in enumerate(names):
        loaded_img_eql(
            loaded_imgs[i],
            name=name,
            success=successful[i],
        )
