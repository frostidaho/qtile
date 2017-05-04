from __future__ import division
import pytest
import libqtile.images as images
import cairocffi
import subprocess as sp
from collections import namedtuple
from os import path
from glob import glob

TEST_DIR = path.dirname(path.abspath(__file__))
DATA_DIR = path.join(TEST_DIR, 'data')
PNGS = glob(path.join(DATA_DIR, '*', '*.png'))
SVGS = glob(path.join(DATA_DIR, '*', '*.svg'))
ALL_IMAGES = glob(path.join(DATA_DIR, '*', '*'))
metrics = ('AE', 'FUZZ', 'MAE', 'MEPP', 'MSE', 'PAE', 'PHASH', 'PSNR', 'RMSE')
ImgDistortion = namedtuple('ImgDistortion', metrics)

def compare_images(test_img, reference_img, metric='MAE'):
    """Compare images at paths test_img and reference_img

    Use imagemagick to calculate distortion using the given metric
    """
    cmd = [
        'convert',
        test_img,
        reference_img,
        '-metric',
        metric,
        '-compare',
        '-format',
        '%[distortion]\n',
        'info:'
    ]
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    stdout, stderr = p.communicate()
    print('stdout', stdout)
    print('stderr', stderr)
    print('cmd', cmd)
    return float(stdout.decode().strip())

def compare_images_all_metrics(test_img, reference_img):
    """Compare images at paths test_img and reference_img

    Use imagemagick to calculate distortion using all metrics
    listed as fields in ImgDistortion.
    """
    vals = []
    for metric in ImgDistortion._fields:
        vals.append(compare_images(test_img, reference_img, metric))
    return ImgDistortion._make(vals)

@pytest.fixture(scope='function', params=SVGS)
def svg_img(request):
    fpath = request.param
    return images.Img.from_path(fpath)

@pytest.fixture(scope='function')
def comparison_images(svg_img):
    name = svg_img.name
    path_good = path.join(DATA_DIR, 'comparison_images', name+'_good.png')
    path_bad = path.join(DATA_DIR, 'comparison_images', name+'_bad.png')
    return path_bad, path_good
    
@pytest.fixture(scope='function')
def distortion_bad(svg_img, comparison_images):
    path_bad, path_good = comparison_images
    name = svg_img.name
    return compare_images_all_metrics(path_bad, path_good)

def assert_distortion_less_than(distortion, bad_distortion, factor=0.9):
    for test_val, bad_val in zip(distortion, bad_distortion):
        assert test_val < (bad_val * factor)

def test_svg_scaling(svg_img, distortion_bad, comparison_images, tmpdir):
    path_bad, path_good = comparison_images
    scaling_factor = 20
    print(svg_img.path)
    print(distortion_bad)
    print(tmpdir.dirpath())
    # assert distortion_bad == 1
    dpath = tmpdir.dirpath

    width, height = svg_img.width, svg_img.height
    name = svg_img.name
    svg_img.lock_aspect_ratio = True
    width *= scaling_factor
    svg_img.width = width
    surf = cairocffi.SVGSurface(str(dpath(name+'.svg')), svg_img.width, svg_img.height)
    ctx = cairocffi.Context(surf)

    ctx.save()
    ctx.set_source(svg_img.pattern)
    ctx.paint()
    ctx.restore()

    test_png_path = str(dpath(name+'.png'))
    surf.write_to_png(test_png_path)
    surf.finish()
    distortion = compare_images_all_metrics(test_png_path, path_good)
    assert_distortion_less_than(distortion, distortion_bad)
