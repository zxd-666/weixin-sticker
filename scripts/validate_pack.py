#!/usr/bin/env python3
"""Validate the measurable parts of a WeChat sticker album directory."""

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from optimize_png import COMPRESSION_THRESHOLD, ICON_LIMIT, SIZES, has_actual_transparency, has_any_transparency

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif"}
SUFFIX_FORMATS = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".gif": "GIF"}
REWARD_ROLES = ("赞赏引导图", "赞赏致谢图")
REWARD_SIZES = {"赞赏引导图": SIZES["reward-guide"], "赞赏致谢图": SIZES["reward-thanks"]}
LEGACY_NAMES = {"banner.png", "banner.jpg", "banner.jpeg", "cover.png", "icon.png", "reward-guide.png", "reward-guide.jpg", "reward-guide.jpeg", "reward-guide.gif", "reward-thanks.png", "reward-thanks.jpg", "reward-thanks.jpeg", "reward-thanks.gif"}


def collect_reward_assets(directory: Path) -> dict[str, list[Path]]:
    files = [path for path in directory.iterdir() if path.is_file()]
    return {role: sorted(path for path in files if path.stem == role) for role in REWARD_ROLES}


def inspect_image(path: Path, formats: set[str], size: tuple[int, int], errors: list[str]):
    try:
        with Image.open(path) as image:
            if image.format not in formats:
                errors.append(f"{path}: expected {', '.join(sorted(formats))}, got {image.format}")
            if image.format != SUFFIX_FORMATS.get(path.suffix.lower()):
                errors.append(f"{path}: file extension does not match image format {image.format}")
            if image.size != size:
                errors.append(f"{path}: expected {size[0]}x{size[1]}, got {image.width}x{image.height}")
            frame_count = getattr(image, "n_frames", 1)
            if frame_count != 1:
                errors.append(f"{path}: animated image is not supported ({frame_count} frames)")
            return image.format, has_actual_transparency(image), has_any_transparency(image)
    except (OSError, UnidentifiedImageError) as error:
        errors.append(f"{path}: cannot read image: {error}")
        return None


def validate_pack(directory: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for path in directory.iterdir():
        if path.is_file() and path.name in LEGACY_NAMES:
            errors.append(f"{path}: rename this asset with its Chinese role name")
    if (directory / "stickers").exists():
        errors.append(f"{directory / 'stickers'}: rename directory to 表情")
    sticker_dir = directory / "表情"
    if not sticker_dir.is_dir():
        errors.append(f"{sticker_dir}: missing 表情 directory")
        stickers = []
    else:
        files = sorted(path for path in sticker_dir.iterdir() if path.is_file() and not path.name.startswith("."))
        stickers = [path for path in files if path.suffix.lower() in IMAGE_SUFFIXES]
        for path in files:
            if path not in stickers:
                errors.append(f"{path}: unsupported file in 表情 directory")
    if not 8 <= len(stickers) <= 24:
        errors.append(f"表情: need 8–24 images, got {len(stickers)}")

    for path in stickers:
        if not re.fullmatch(r"[\u4e00-\u9fff]{1,4}", path.stem):
            errors.append(f"{path}: sticker filename must be a Chinese theme of at most 4 characters")
        result = inspect_image(path, {"PNG"}, SIZES["sticker"], errors)
        if result is None:
            continue
        image_format, transparent, _ = result
        if image_format == "PNG" and not transparent:
            warnings.append(f"{path}: PNG sticker is opaque; review its background")
        if path.stat().st_size > COMPRESSION_THRESHOLD:
            warnings.append(f"{path}: above 500KB, platform may compress it")

    banners = [directory / name for name in ("详情页横幅.png", "详情页横幅.jpg", "详情页横幅.jpeg") if (directory / name).is_file()]
    if len(banners) != 1:
        errors.append(f"详情页横幅: need exactly one PNG or JPG, got {len(banners)}")
    else:
        path = banners[0]
        result = inspect_image(path, {"PNG", "JPEG"}, SIZES["banner"], errors)
        if result and result[2]:
            errors.append(f"{path}: banner must be opaque")
        if path.stat().st_size > COMPRESSION_THRESHOLD:
            warnings.append(f"{path}: above 500KB, platform may compress it")

    for name, mode in (("表情封面.png", "cover"), ("聊天页图标.png", "icon")):
        path = directory / name
        if not path.is_file():
            errors.append(f"{path}: missing")
            continue
        result = inspect_image(path, {"PNG"}, SIZES[mode], errors)
        if result and not result[1]:
            errors.append(f"{path}: needs real transparent pixels")
        file_size = path.stat().st_size
        if mode == "icon" and file_size >= ICON_LIMIT:
            errors.append(f"{path}: must be <100KB")
        if mode == "cover" and file_size > COMPRESSION_THRESHOLD:
            warnings.append(f"{path}: above 500KB, platform may compress it")

    reward_assets = collect_reward_assets(directory)
    if any(reward_assets.values()) and not all(reward_assets.values()):
        errors.append("赞赏素材: 赞赏引导图 and 赞赏致谢图 must both be present")
    for role, paths in reward_assets.items():
        if len(paths) > 1:
            errors.append(f"{role}: need exactly one image, got {len(paths)}")
        if len(paths) != 1:
            continue
        path = paths[0]
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            errors.append(f"{path}: reward image must be JPG, GIF or PNG")
            continue
        inspect_image(path, {"PNG", "JPEG", "GIF"}, REWARD_SIZES[role], errors)
        if path.stat().st_size > COMPRESSION_THRESHOLD:
            warnings.append(f"{path}: above 500KB, platform may compress it")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("album_dir", type=Path)
    args = parser.parse_args()
    if not args.album_dir.is_dir():
        parser.error(f"album directory not found: {args.album_dir}")
    errors, warnings = validate_pack(args.album_dir)
    for warning in warnings:
        print("WARNING: " + warning, file=sys.stderr)
    for error in errors:
        print("ERROR: " + error, file=sys.stderr)
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK: album files passed measurable checks ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
