#!/usr/bin/env python3
"""Prepare exact-size PNG assets for a WeChat sticker album."""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

SIZES = {
    "sticker": (240, 240),
    "cover": (240, 240),
    "icon": (50, 50),
    "banner": (750, 400),
    "reward-guide": (750, 560),
    "reward-thanks": (750, 750),
}
COMPRESSION_THRESHOLD = 500 * 1024
ICON_LIMIT = 100 * 1024  # user-supplied rule is strictly smaller than 100KB


def has_actual_transparency(img: Image.Image) -> bool:
    alpha = img.convert("RGBA").getchannel("A")
    minimum, maximum = alpha.getextrema()
    return minimum == 0 and maximum > 0


def has_any_transparency(img: Image.Image) -> bool:
    return img.convert("RGBA").getchannel("A").getextrema()[0] < 255


def fit_on_transparent_canvas(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    work = img.convert("RGBA")
    work.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(work, ((size[0] - work.width) // 2, (size[1] - work.height) // 2))
    return canvas


def prepare(img: Image.Image, mode: str) -> Image.Image:
    if mode == "banner":
        if has_any_transparency(img):
            raise ValueError("banner must have an opaque background")
        # Preserve proportions; a non-matching source ratio is cropped, never stretched.
        return ImageOps.fit(img.convert("RGB"), SIZES[mode], Image.Resampling.LANCZOS)
    if mode in ("reward-guide", "reward-thanks"):
        color_mode = "RGBA" if has_any_transparency(img) else "RGB"
        return ImageOps.fit(img.convert(color_mode), SIZES[mode], Image.Resampling.LANCZOS)
    if not has_actual_transparency(img):
        raise ValueError(f"{mode} input needs real transparent pixels; remove its background first")
    return fit_on_transparent_canvas(img, SIZES[mode])


def validate(path: Path, mode: str, max_kb: int | None = None) -> list[str]:
    errors = []
    with Image.open(path) as img:
        if img.format != "PNG":
            errors.append(f"{mode} must be PNG")
        if img.size != SIZES[mode]:
            errors.append(f"{mode} must be {SIZES[mode][0]}x{SIZES[mode][1]}, got {img.width}x{img.height}")
        if mode == "banner":
            if has_any_transparency(img):
                errors.append("banner must have an opaque background")
        elif mode in ("reward-guide", "reward-thanks"):
            pass
        elif not has_actual_transparency(img):
            errors.append(f"{mode} must contain real transparent pixels")
    size = path.stat().st_size
    if mode == "icon" and size >= ICON_LIMIT:
        errors.append(f"icon must be <100KB, got {size / 1024:.1f}KB")
    if max_kb is not None and size > max_kb * 1024:
        errors.append(f"file must be <={max_kb}KB, got {size / 1024:.1f}KB")
    return errors


def save_png(img: Image.Image, out: Path, mode: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG", optimize=True, compress_level=9)
    if mode == "icon" and out.stat().st_size >= ICON_LIMIT:
        pal = img.quantize(colors=128, method=Image.Quantize.FASTOCTREE)
        pal.save(out, format="PNG", optimize=True, compress_level=9)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("--mode", choices=tuple(SIZES), required=True)
    parser.add_argument("--check", action="store_true", help="Validate only.")
    parser.add_argument("--max-kb", type=int, default=None, help="Optional strict size ceiling.")
    args = parser.parse_args()
    if not args.input.is_file():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2
    if args.max_kb is not None and args.max_kb <= 0:
        parser.error("--max-kb must be positive")
    if args.check:
        path = args.input
    else:
        if args.output is None:
            parser.error("output path is required unless --check is used")
        if args.output.suffix.lower() != ".png":
            parser.error("this script writes PNG only; use a .png output path")
        try:
            with Image.open(args.input) as source:
                result = prepare(source, args.mode)
            save_png(result, args.output, args.mode)
        except (OSError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1
        path = args.output
    try:
        errors = validate(path, args.mode, args.max_kb)
    except OSError as error:
        print(str(error), file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    size = path.stat().st_size
    if args.mode != "icon" and size > COMPRESSION_THRESHOLD:
        print(f"warning: {path} is above 500KB and may be compressed by the platform", file=sys.stderr)
    print("OK" if args.check else f"saved {path} ({size / 1024:.1f}KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
