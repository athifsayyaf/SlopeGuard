from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"E:\Lenovo_path_moved\moved_due_to_storageissue\New project")
FRONTEND_ASSETS = ROOT / "slideagent-ai" / "frontend" / "assets"
DELIVERY = ROOT / "SlopeGuard_AI_Delivery_v2"
LAUNCHER = DELIVERY / "launcher"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for name in names:
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def make_icon(size: int) -> Image.Image:
    scale = size / 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(44 * scale)
    pad = int(12 * scale)
    d.rounded_rectangle((pad, pad, size - pad, size - pad), radius=r, fill=(248, 250, 246, 255), outline=(205, 219, 207, 255), width=max(1, int(3 * scale)))

    mountain = [
        (int(38 * scale), int(176 * scale)),
        (int(86 * scale), int(92 * scale)),
        (int(116 * scale), int(132 * scale)),
        (int(164 * scale), int(62 * scale)),
        (int(220 * scale), int(176 * scale)),
    ]
    d.polygon(mountain, fill=(47, 125, 79, 255))
    d.polygon([(int(86 * scale), int(92 * scale)), (int(116 * scale), int(132 * scale)), (int(98 * scale), int(132 * scale))], fill=(221, 231, 186, 255))
    d.polygon([(int(164 * scale), int(62 * scale)), (int(220 * scale), int(176 * scale)), (int(138 * scale), int(176 * scale))], fill=(122, 163, 90, 255))

    slide = [(int(91 * scale), int(178 * scale)), (int(117 * scale), int(134 * scale)), (int(158 * scale), int(105 * scale)), (int(198 * scale), int(54 * scale))]
    d.line(slide, fill=(181, 72, 51, 255), width=max(5, int(15 * scale)), joint="curve")
    d.line((int(43 * scale), int(180 * scale), int(215 * scale), int(180 * scale)), fill=(31, 53, 40, 255), width=max(3, int(9 * scale)))

    # Small contour lines, inspired by GIS icon sets without copying any specific glyph.
    d.line((int(58 * scale), int(72 * scale), int(100 * scale), int(72 * scale)), fill=(111, 139, 118, 255), width=max(2, int(6 * scale)))
    d.line((int(68 * scale), int(54 * scale), int(94 * scale), int(54 * scale)), fill=(111, 139, 118, 255), width=max(2, int(5 * scale)))

    if size >= 128:
        text = "SG"
        f = font(max(12, int(25 * scale)), True)
        bbox = d.textbbox((0, 0), text, font=f)
        d.text(((size - (bbox[2] - bbox[0])) / 2, int(210 * scale)), text, fill=(31, 53, 40, 255), font=f)
    return img


def main() -> None:
    FRONTEND_ASSETS.mkdir(parents=True, exist_ok=True)
    LAUNCHER.mkdir(parents=True, exist_ok=True)
    DELIVERY.mkdir(parents=True, exist_ok=True)

    sizes = [16, 24, 32, 48, 64, 128, 256]
    icon_images = [make_icon(size) for size in sizes]
    icon_images[-1].save(FRONTEND_ASSETS / "slopeguard.ico", sizes=[(s, s) for s in sizes])
    icon_images[-1].save(LAUNCHER / "slopeguard.ico", sizes=[(s, s) for s in sizes])
    for size in [192, 512]:
        make_icon(size).save(FRONTEND_ASSETS / f"slopeguard-icon-{size}.png")
    make_icon(512).save(DELIVERY / "SlopeGuard_AI_logo.png")
    print("Created SlopeGuard icon assets.")


if __name__ == "__main__":
    main()
