import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from PIL import Image

PACKAGER = Path(__file__).resolve().parents[1] / "scripts" / "package_album.py"
THEMES = ["开心", "生气", "惊喜", "鼓掌", "抱抱", "晚安", "收到", "加油"]


def make_album(root):
    stickers = root / "表情"
    stickers.mkdir()
    for theme in THEMES:
        image = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        image.paste((80, 120, 220, 255), (40, 40, 200, 200))
        image.save(stickers / f"{theme}.png")
    for filename, size in (("表情封面.png", (240, 240)), ("聊天页图标.png", (50, 50))):
        image = Image.new("RGBA", size, (0, 0, 0, 0))
        image.paste((80, 120, 220, 255), (10, 10, size[0] - 10, size[1] - 10))
        image.save(root / filename)
    Image.new("RGB", (750, 400), (20, 120, 180)).save(root / "详情页横幅.png")
    return stickers


def run_packager(root, output):
    return subprocess.run([sys.executable, str(PACKAGER), str(root), str(output)], text=True, capture_output=True)


def test_package_contains_only_approved_album_files(tmp_path):
    album = tmp_path / "album"
    album.mkdir()
    make_album(album)
    (album / "说明.txt").write_text("draft", encoding="utf-8")
    output = tmp_path / "专辑.zip"
    result = run_packager(album, output)
    assert result.returncode == 0, result.stderr
    with ZipFile(output) as archive:
        assert sorted(archive.namelist()) == sorted([*(f"表情/{theme}.png" for theme in THEMES), "详情页横幅.png", "表情封面.png", "聊天页图标.png"])


def test_package_rejects_invalid_album_and_numeric_names(tmp_path):
    album = tmp_path / "album"
    album.mkdir()
    stickers = make_album(album)
    (stickers / "开心.png").rename(stickers / "01.png")
    output = tmp_path / "专辑.zip"
    result = run_packager(album, output)
    assert result.returncode != 0
    assert "Chinese theme" in result.stderr
    assert not output.exists()
    (stickers / "01.png").rename(stickers / "开心.png")
    (album / "表情封面.png").unlink()
    result = run_packager(album, output)
    assert result.returncode != 0
    assert "validation failed" in result.stderr
    assert not output.exists()


def test_package_includes_confirmed_reward_pair(tmp_path):
    album = tmp_path / "album"
    album.mkdir()
    make_album(album)
    Image.new("RGB", (750, 560), (30, 100, 150)).save(album / "赞赏引导图.jpg")
    Image.new("RGB", (750, 750), (30, 100, 150)).save(album / "赞赏致谢图.png")
    output = tmp_path / "专辑.zip"
    result = run_packager(album, output)
    assert result.returncode == 0, result.stderr
    with ZipFile(output) as archive:
        names = archive.namelist()
    assert len(names) == len(THEMES) + 5
    assert "赞赏引导图.jpg" in names
    assert "赞赏致谢图.png" in names


def test_package_refuses_incomplete_reward_pair(tmp_path):
    album = tmp_path / "album"
    album.mkdir()
    make_album(album)
    Image.new("RGB", (750, 560), (30, 100, 150)).save(album / "赞赏引导图.png")
    output = tmp_path / "专辑.zip"
    result = run_packager(album, output)
    assert result.returncode != 0
    assert "must both be present" in result.stderr
    assert not output.exists()


def test_package_refuses_english_zip_name(tmp_path):
    album = tmp_path / "专辑"
    album.mkdir()
    make_album(album)
    output = tmp_path / "album.zip"
    result = run_packager(album, output)
    assert result.returncode != 0
    assert "ZIP filename must use Chinese" in result.stderr
    assert not output.exists()


def test_package_refuses_english_sticker_name(tmp_path):
    album = tmp_path / "专辑"
    album.mkdir()
    stickers = make_album(album)
    (stickers / "开心.png").rename(stickers / "happy.png")
    output = tmp_path / "专辑.zip"
    result = run_packager(album, output)
    assert result.returncode != 0
    assert "Chinese theme" in result.stderr
    assert not output.exists()
