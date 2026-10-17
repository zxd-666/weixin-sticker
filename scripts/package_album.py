#!/usr/bin/env python3
"""Validate and package an approved static WeChat sticker album."""

import argparse
import re
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from validate_pack import collect_reward_assets, validate_pack


def package_album(directory: Path, output: Path) -> None:
    if not directory.is_dir():
        raise ValueError(f"album directory not found: {directory}")
    errors, warnings = validate_pack(directory)
    for warning in warnings:
        print("WARNING: " + warning, file=sys.stderr)
    if errors:
        raise ValueError("album validation failed:\n" + "\n".join(errors))

    stickers = sorted(path for path in (directory / "表情").iterdir() if path.is_file() and path.suffix.lower() == ".png")
    bad_names = [path.name for path in stickers if not re.fullmatch(r"[\u4e00-\u9fff]{1,4}", path.stem)]
    if bad_names:
        raise ValueError("sticker filenames must be Chinese theme names of at most 4 characters: " + ", ".join(bad_names))

    if not re.search(r"[\u4e00-\u9fff]", output.stem) or any(char.isascii() and char.isalnum() for char in output.stem):
        raise ValueError("ZIP filename must use Chinese words and may not contain English letters or digits")

    banners = [directory / name for name in ("详情页横幅.png", "详情页横幅.jpg", "详情页横幅.jpeg") if (directory / name).is_file()]
    members = [*stickers, banners[0], directory / "表情封面.png", directory / "聊天页图标.png"]
    reward_assets = collect_reward_assets(directory)
    if reward_assets["赞赏引导图"]:
        members.extend((reward_assets["赞赏引导图"][0], reward_assets["赞赏致谢图"][0]))
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
        for path in members:
            archive.write(path, path.relative_to(directory).as_posix())
    print(f"saved {output} ({len(stickers)} stickers, {len(members)} files)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("album_dir", type=Path)
    parser.add_argument("output_zip", type=Path)
    args = parser.parse_args()
    if args.output_zip.suffix.lower() != ".zip":
        parser.error("output path must end with .zip")
    try:
        package_album(args.album_dir, args.output_zip)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
