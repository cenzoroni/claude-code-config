#!/usr/bin/env python3
"""Generate Play Store visual assets from app config.

Generates:
  - 512x512 hi-res icon from a source image
  - 1024x500 feature graphic with icon + app name
  - Screenshots via adb from a running emulator (optional)
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

import yaml

from user_config import app_slug, apply_user_config
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent

# Fonts — prefer clean sans-serif, fall back through macOS system fonts
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Futura.ttc",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
]

# Feature graphic defaults
DEFAULT_BG_GRADIENT = ("#0D47A1", "#1565C0")  # dark blue to medium blue
DEFAULT_TEXT_COLOR = "#FFFFFF"
DEFAULT_TAGLINE_COLOR = "#B3D4FC"


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return apply_user_config(config, slug=app_slug(config, config_path))


def find_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def get_dominant_colors(img: Image.Image) -> tuple[str, str]:
    """Extract two dominant colors from an image for the gradient background."""
    small = img.resize((50, 50)).convert("RGB")
    pixels = list(small.get_flattened_data()
                  if hasattr(small, "get_flattened_data")
                  else small.getdata())
    non_black = [(r, g, b) for r, g, b in pixels if r + g + b > 30]
    if not non_black:
        return DEFAULT_BG_GRADIENT

    avg_r = sum(p[0] for p in non_black) // len(non_black)
    avg_g = sum(p[1] for p in non_black) // len(non_black)
    avg_b = sum(p[2] for p in non_black) // len(non_black)

    dark = (max(0, avg_r - 40), max(0, avg_g - 40), max(0, avg_b - 40))
    light = (min(255, avg_r + 20), min(255, avg_g + 20), min(255, avg_b + 20))
    return (f"#{dark[0]:02x}{dark[1]:02x}{dark[2]:02x}",
            f"#{light[0]:02x}{light[1]:02x}{light[2]:02x}")


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def make_gradient(width: int, height: int, color1: str, color2: str) -> Image.Image:
    """Create a horizontal gradient image."""
    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)
    img = Image.new("RGB", (width, height))
    for x in range(width):
        ratio = x / (width - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        for y in range(height):
            img.putpixel((x, y), (r, g, b))
    return img


def generate_icon(source_path: Path, output_path: Path) -> None:
    """Crop and resize source image to 512x512 Play Store icon."""
    img = Image.open(source_path).convert("RGBA")
    w, h = img.size

    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    cropped = img.crop((left, top, left + side, top + side))

    icon = cropped.resize((512, 512), Image.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    icon.save(str(output_path), "PNG")
    print(f"Icon: {output_path} (512x512)")


def generate_feature_graphic(
    source_path: Path,
    app_name: str,
    output_path: Path,
    tagline: str | None = None,
    bg_colors: tuple[str, str] | None = None,
    text_color: str = DEFAULT_TEXT_COLOR,
) -> None:
    """Generate a 1024x500 feature graphic with icon + app name."""
    W, H = 1024, 500

    icon_img = Image.open(source_path).convert("RGBA")

    if bg_colors is None:
        bg_colors = get_dominant_colors(icon_img)

    bg = make_gradient(W, H, bg_colors[0], bg_colors[1])

    icon_size = 200
    side = min(icon_img.size)
    left = (icon_img.width - side) // 2
    top = (icon_img.height - side) // 2
    icon_cropped = icon_img.crop((left, top, left + side, top + side))
    icon_resized = icon_cropped.resize((icon_size, icon_size), Image.LANCZOS)

    shadow = Image.new("RGBA", (icon_size + 8, icon_size + 8), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        [0, 0, icon_size + 7, icon_size + 7],
        radius=32,
        fill=(0, 0, 0, 80),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))

    icon_x = 120
    icon_y = (H - icon_size) // 2

    bg_rgba = bg.convert("RGBA")
    bg_rgba.paste(shadow, (icon_x - 4, icon_y + 4), shadow)
    bg_rgba.paste(icon_resized, (icon_x, icon_y), icon_resized)

    draw = ImageDraw.Draw(bg_rgba)

    title_font = find_font(72)
    text_x = icon_x + icon_size + 60
    max_text_w = W - text_x - 40
    text_color_rgb = hex_to_rgb(text_color)

    title_bbox = draw.textbbox((0, 0), app_name, font=title_font)
    title_h = title_bbox[3] - title_bbox[1]

    if tagline:
        tagline_font = find_font(24)
        # Word-wrap the tagline to fit
        words = tagline.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            tw = draw.textbbox((0, 0), test, font=tagline_font)[2]
            if tw > max_text_w and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        wrapped = "\n".join(lines[:2])  # max 2 lines

        tagline_bbox = draw.multiline_textbbox((0, 0), wrapped, font=tagline_font)
        tagline_h = tagline_bbox[3] - tagline_bbox[1]
        total_h = title_h + 20 + tagline_h
        title_y = (H - total_h) // 2
        tagline_y = title_y + title_h + 20
        tagline_color = hex_to_rgb(DEFAULT_TAGLINE_COLOR)
        draw.multiline_text(
            (text_x, tagline_y), wrapped,
            fill=tagline_color, font=tagline_font, spacing=6,
        )
    else:
        title_y = (H - title_h) // 2

    draw.text((text_x, title_y), app_name, fill=text_color_rgb, font=title_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    bg_rgba.convert("RGB").save(str(output_path), "PNG")
    print(f"Feature graphic: {output_path} (1024x500)")


def capture_screenshots(
    project_path: Path,
    output_dir: Path,
    screens: list[str] | None = None,
    emulator_id: str | None = None,
) -> list[Path]:
    """Capture screenshots from a running emulator via adb."""
    output_dir.mkdir(parents=True, exist_ok=True)

    adb = "adb"
    if emulator_id:
        adb = f"adb -s {emulator_id}"

    result = subprocess.run(
        f"{adb} devices", shell=True, capture_output=True, text=True,
    )
    devices = [
        line.split("\t")[0]
        for line in result.stdout.strip().splitlines()[1:]
        if "emulator" in line and "device" in line
    ]
    if not devices:
        print("No emulator running. Start one with: flutter emulators --launch <id>", file=sys.stderr)
        return []

    device = emulator_id or devices[0]
    adb = f"adb -s {device}"

    captured = []
    idx = 1

    def take_screenshot(name: str) -> Path | None:
        nonlocal idx
        remote = f"/sdcard/screenshot_{idx}.png"
        local = output_dir / f"screenshot_{idx:02d}_{name}.png"

        subprocess.run(f"{adb} shell screencap -p {remote}", shell=True, check=True)
        subprocess.run(f"{adb} pull {remote} {local}", shell=True, check=True,
                       capture_output=True)
        subprocess.run(f"{adb} shell rm {remote}", shell=True, capture_output=True)

        if local.exists():
            print(f"Screenshot {idx}: {local}")
            idx += 1
            return local
        return None

    print("Waiting 3s for UI to settle...")
    time.sleep(3)

    path = take_screenshot("home")
    if path:
        captured.append(path)

    if screens:
        for screen in screens:
            input(f"\nNavigate to '{screen}', then press Enter to capture...")
            path = take_screenshot(screen.replace(" ", "_").lower())
            if path:
                captured.append(path)

    print(f"\nCaptured {len(captured)} screenshot(s) in {output_dir}")
    return captured


def auto_capture_screenshots(
    project_path: Path,
    output_dir: Path,
    emulator_id: str | None = None,
) -> list[Path]:
    """Capture screenshots non-interactively — just captures current screen."""
    output_dir.mkdir(parents=True, exist_ok=True)

    adb = "adb"
    if emulator_id:
        adb = f"adb -s {emulator_id}"

    result = subprocess.run(
        f"{adb} devices", shell=True, capture_output=True, text=True,
    )
    devices = [
        line.split("\t")[0]
        for line in result.stdout.strip().splitlines()[1:]
        if "emulator" in line and "device" in line
    ]
    if not devices:
        print("No emulator running.", file=sys.stderr)
        return []

    device = emulator_id or devices[0]
    adb = f"adb -s {device}"

    remote = "/sdcard/screenshot.png"
    local = output_dir / "screenshot.png"

    subprocess.run(f"{adb} shell screencap -p {remote}", shell=True, check=True)
    subprocess.run(f"{adb} pull {remote} {local}", shell=True, check=True,
                   capture_output=True)
    subprocess.run(f"{adb} shell rm {remote}", shell=True, capture_output=True)

    if local.exists():
        print(f"Screenshot: {local}")
        return [local]
    return []


def main():
    parser = argparse.ArgumentParser(description="Generate Play Store visual assets")
    parser.add_argument("--config", required=True, help="Path to app YAML config")
    parser.add_argument("--project", help="Path to Flutter project root (overrides config repo)")
    parser.add_argument("--output", help="Output directory (default: project-root/store_assets/)")
    parser.add_argument(
        "command",
        choices=["icon", "feature", "screenshots", "all"],
        help="Which asset(s) to generate",
    )
    parser.add_argument("--emulator", help="Emulator serial (from adb devices)")
    parser.add_argument("--interactive", action="store_true",
                        help="Interactive screenshot mode — pause between screens")
    args = parser.parse_args()

    config = load_config(args.config)
    app = config.get("app", {})
    store_assets = config.get("store_assets", {})

    project = Path(args.project or app.get("repo", ".")).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve() if args.output else project / "store_assets"
    output_dir.mkdir(parents=True, exist_ok=True)

    icon_source = store_assets.get("icon_source")
    if icon_source:
        icon_source = project / icon_source

    if args.command in ("icon", "all"):
        if not icon_source or not icon_source.exists():
            print(f"Error: icon source not found at {icon_source}", file=sys.stderr)
            if args.command == "icon":
                sys.exit(1)
        else:
            generate_icon(icon_source, output_dir / "icon_512.png")

    if args.command in ("feature", "all"):
        if not icon_source or not icon_source.exists():
            print(f"Error: icon source not found at {icon_source}", file=sys.stderr)
            if args.command == "feature":
                sys.exit(1)
        else:
            bg = None
            fg_cfg = store_assets.get("feature_graphic", {})
            if isinstance(fg_cfg, dict):
                bg_from = fg_cfg.get("bg_gradient")
                if isinstance(bg_from, list) and len(bg_from) == 2:
                    bg = tuple(bg_from)

            generate_feature_graphic(
                source_path=icon_source,
                app_name=app.get("name", "App"),
                output_path=output_dir / "feature_graphic.png",
                tagline=app.get("description_short"),
                bg_colors=bg,
            )

    if args.command in ("screenshots", "all"):
        screens = config.get("screens", [])
        if args.interactive:
            capture_screenshots(project, output_dir / "screenshots", screens, args.emulator)
        else:
            auto_capture_screenshots(project, output_dir / "screenshots", args.emulator)


if __name__ == "__main__":
    main()
