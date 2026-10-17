import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'optimize_png.py'


def make_rgba(path: Path, size=(300, 300)):
    img = Image.new('RGBA', size, (255, 0, 0, 0))
    # Draw a simple opaque center block so transparency is preserved around it.
    for x in range(size[0] // 4, size[0] * 3 // 4):
        for y in range(size[1] // 4, size[1] * 3 // 4):
            img.putpixel((x, y), (20, 80, 180, 255))
    img.save(path)


def run_script(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], text=True, capture_output=True)


def test_icon_mode_outputs_50x50_rgba_under_100kb():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / 'src.png'
        out = Path(td) / 'icon.png'
        make_rgba(src, (300, 240))
        r = run_script(src, out, '--mode', 'icon')
        assert r.returncode == 0, r.stderr
        img = Image.open(out)
        assert img.size == (50, 50)
        assert img.mode == 'RGBA'
        assert os.path.getsize(out) <= 100 * 1024


def test_sticker_mode_outputs_exact_240_square_and_preserves_alpha():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / 'src.png'
        out = Path(td) / 'sticker.png'
        make_rgba(src, (640, 320))
        r = run_script(src, out, '--mode', 'sticker')
        assert r.returncode == 0, r.stderr
        img = Image.open(out)
        assert img.size == (240, 240)
        assert img.mode == 'RGBA'


def test_check_mode_fails_for_oversized_icon():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / 'bad.png'
        make_rgba(src, (64, 64))
        r = run_script(src, '--check', '--mode', 'icon')
        assert r.returncode != 0
        assert '50x50' in (r.stdout + r.stderr)


def test_opaque_input_is_rejected_for_transparent_assets():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / 'opaque.png'
        out = Path(td) / 'sticker.png'
        Image.new('RGB', (480, 480), 'white').save(src)
        r = run_script(src, out, '--mode', 'sticker')
        assert r.returncode != 0
        assert 'real transparent pixels' in r.stderr


def test_cover_and_banner_have_distinct_background_rules():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        transparent = td / 'transparent.png'
        opaque = td / 'opaque.png'
        make_rgba(transparent, (360, 300))
        Image.new('RGB', (1000, 600), (20, 120, 80)).save(opaque)
        cover = td / 'cover.png'
        banner = td / 'banner.png'
        assert run_script(transparent, cover, '--mode', 'cover').returncode == 0
        assert Image.open(cover).size == (240, 240)
        assert run_script(opaque, banner, '--mode', 'banner').returncode == 0
        assert Image.open(banner).size == (750, 400)
        assert run_script(transparent, td / 'bad-banner.png', '--mode', 'banner').returncode != 0
        translucent = td / 'translucent.png'
        Image.new('RGBA', (750, 400), (20, 120, 80, 128)).save(translucent)
        assert run_script(translucent, td / 'bad-banner-2.png', '--mode', 'banner').returncode != 0


def test_reward_modes_preserve_proportions_and_allow_opaque_or_transparent_sources(tmp_path):
    opaque = tmp_path / 'opaque.png'
    transparent = tmp_path / 'transparent.png'
    guide = tmp_path / 'reward-guide.png'
    thanks = tmp_path / 'reward-thanks.png'
    Image.new('RGB', (1200, 700), (20, 120, 80)).save(opaque)
    make_rgba(transparent, (500, 800))
    assert run_script(opaque, guide, '--mode', 'reward-guide').returncode == 0
    assert run_script(transparent, thanks, '--mode', 'reward-thanks').returncode == 0
    with Image.open(guide) as image:
        assert image.size == (750, 560)
        assert image.mode == 'RGB'
    with Image.open(thanks) as image:
        assert image.size == (750, 750)
        assert image.mode == 'RGBA'
