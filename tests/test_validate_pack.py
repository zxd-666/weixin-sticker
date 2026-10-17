import subprocess
import sys
from pathlib import Path

from PIL import Image

VALIDATOR = Path(__file__).resolve().parents[1] / "scripts" / "validate_pack.py"


def transparent_asset(path, size):
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    image.paste((30, 100, 190, 255), (size[0] // 4, size[1] // 4, size[0] * 3 // 4, size[1] * 3 // 4))
    image.save(path)


def make_pack(root):
    stickers = root / "表情"
    stickers.mkdir()
    for theme in ("开心", "生气", "惊喜", "鼓掌", "抱抱", "晚安", "收到", "加油"):
        transparent_asset(stickers / f"{theme}.png", (240, 240))
    transparent_asset(root / "表情封面.png", (240, 240))
    transparent_asset(root / "聊天页图标.png", (50, 50))
    Image.new("RGB", (750, 400), (30, 130, 180)).save(root / "详情页横幅.png")
    return stickers


def run_validator(root):
    return subprocess.run([sys.executable, str(VALIDATOR), str(root)], text=True, capture_output=True)


def test_valid_static_pack(tmp_path):
    make_pack(tmp_path)
    result = run_validator(tmp_path)
    assert result.returncode == 0, result.stderr


def test_pack_rejects_animated_gif(tmp_path):
    stickers = make_pack(tmp_path)
    frames = [Image.new("RGB", (240, 240), color) for color in ("red", "blue")]
    frames[0].save(stickers / "开心.gif", save_all=True, append_images=frames[1:], duration=100, loop=0)
    (stickers / "开心.png").unlink()
    result = run_validator(tmp_path)
    assert result.returncode != 0
    assert "expected PNG" in result.stderr


def test_pack_rejects_opaque_cover_and_missing_banner(tmp_path):
    make_pack(tmp_path)
    Image.new("RGB", (240, 240), "white").save(tmp_path / "表情封面.png")
    (tmp_path / "详情页横幅.png").unlink()
    result = run_validator(tmp_path)
    assert result.returncode != 0
    assert "needs real transparent pixels" in result.stderr
    assert "详情页横幅:" in result.stderr


def test_pack_rejects_translucent_banner(tmp_path):
    make_pack(tmp_path)
    Image.new("RGBA", (750, 400), (20, 100, 160, 128)).save(tmp_path / "详情页横幅.png")
    result = run_validator(tmp_path)
    assert result.returncode != 0
    assert "banner must be opaque" in result.stderr


def test_pack_rejects_static_gif_too(tmp_path):
    stickers = make_pack(tmp_path)
    Image.new("RGB", (240, 240), "red").save(stickers / "开心.gif")
    (stickers / "开心.png").unlink()
    result = run_validator(tmp_path)
    assert result.returncode != 0
    assert "expected PNG" in result.stderr


def test_opaque_static_png_is_warning_not_failure(tmp_path):
    stickers = make_pack(tmp_path)
    Image.new("RGB", (240, 240), "white").save(stickers / "开心.png")
    result = run_validator(tmp_path)
    assert result.returncode == 0
    assert "review its background" in result.stderr


def test_valid_reward_pair_accepts_static_png_and_single_frame_gif(tmp_path):
    make_pack(tmp_path)
    Image.new("RGB", (750, 560), (40, 100, 170)).save(tmp_path / "赞赏引导图.png")
    Image.new("RGB", (750, 750), (40, 100, 170)).save(tmp_path / "赞赏致谢图.gif")
    result = run_validator(tmp_path)
    assert result.returncode == 0, result.stderr


def test_reward_pair_is_required_together_and_must_have_exact_size(tmp_path):
    make_pack(tmp_path)
    Image.new("RGB", (750, 560), (40, 100, 170)).save(tmp_path / "赞赏引导图.png")
    result = run_validator(tmp_path)
    assert result.returncode != 0
    assert "must both be present" in result.stderr
    Image.new("RGB", (750, 560), (40, 100, 170)).save(tmp_path / "赞赏致谢图.png")
    result = run_validator(tmp_path)
    assert result.returncode != 0
    assert "expected 750x750" in result.stderr


def test_reward_rejects_animated_gif_and_duplicate_formats(tmp_path):
    make_pack(tmp_path)
    frames = [Image.new("RGB", (750, 560), color) for color in ("red", "blue")]
    frames[0].save(tmp_path / "赞赏引导图.gif", save_all=True, append_images=frames[1:], duration=100, loop=0)
    Image.new("RGB", (750, 750), "green").save(tmp_path / "赞赏致谢图.png")
    result = run_validator(tmp_path)
    assert result.returncode != 0
    assert "animated image is not supported" in result.stderr
    Image.new("RGB", (750, 560), "green").save(tmp_path / "赞赏引导图.png")
    result = run_validator(tmp_path)
    assert result.returncode != 0
    assert "need exactly one image" in result.stderr
