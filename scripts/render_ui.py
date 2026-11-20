#!/usr/bin/env python3
"""Dark terminal still, 920x420. Prompt + hexdump of samples/hello.bin."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "screenshots" / "ui.png"
GOLDEN = ROOT / "tests" / "golden.txt"
SAMPLE = ROOT / "samples" / "hello.bin"

W, H = 920, 420
BG = (13, 17, 23)
CHROME = (22, 27, 34)
BORDER = (48, 54, 61)
PROMPT_USER = (126, 231, 135)
PROMPT_PATH = (121, 192, 255)
PROMPT_CMD = (230, 237, 243)
OFFSET = (210, 168, 91)
HEX = (201, 209, 217)
PIPE = (110, 118, 129)
ASCII = (158, 203, 255)
DOT = (139, 148, 158)
CURSOR = (230, 237, 243)

FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\cascadiamono.ttf"),
    Path(r"C:\Windows\Fonts\CascadiaMono.ttf"),
    Path(r"C:\Windows\Fonts\consola.ttf"),
    Path(r"C:\Windows\Fonts\cour.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"),
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in FONT_CANDIDATES:
        if p.is_file():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def hexdump_c(data: bytes) -> str:
    lines: list[str] = []
    offset = 0
    n = len(data)
    while offset < n:
        chunk = data[offset : offset + 16]
        parts = [f"{offset:08x}  "]
        for i in range(16):
            if i == 8:
                parts.append(" ")
            if i < len(chunk):
                parts.append(f"{chunk[i]:02x} ")
            else:
                parts.append("   ")
        parts.append(" |")
        for b in chunk:
            parts.append(chr(b) if 0x20 <= b <= 0x7E else ".")
        parts.append("|\n")
        lines.append("".join(parts))
        offset += len(chunk)
    lines.append(f"{offset:08x}\n")
    return "".join(lines)


def dump_text() -> str:
    if GOLDEN.is_file():
        return GOLDEN.read_text(encoding="ascii")
    return hexdump_c(SAMPLE.read_bytes())


def draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill) -> int:
    draw.text(xy, text, font=font, fill=fill)
    box = draw.textbbox(xy, text, font=font)
    return box[2]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    font = load_font(15)
    font_sm = load_font(13)

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.ImageDraw(img)

    draw.rounded_rectangle((16, 16, W - 16, H - 16), radius=10, fill=CHROME, outline=BORDER, width=1)
    draw.rectangle((16, 16, W - 16, 52), fill=(30, 35, 43))
    draw.line((16, 52, W - 16, 52), fill=BORDER, width=1)

    for x, c in ((36, (255, 95, 86)), (56, (255, 189, 46)), (76, (39, 201, 63))):
        draw.ellipse((x, 28, x + 12, 40), fill=c)

    draw_text(draw, (100, 26), "user@linux: ~/nasmhex", font_sm, (139, 148, 158))

    dump_lines = [ln.rstrip("\n") for ln in dump_text().splitlines()]
    if len(dump_lines) > 12:
        dump_lines = dump_lines[:11] + dump_lines[-1:]

    x0, y = 36, 70
    line_h = 26

    x = x0
    x = draw_text(draw, (x, y), "user", font, PROMPT_USER)
    x = draw_text(draw, (x, y), "@linux", font, PROMPT_USER)
    x = draw_text(draw, (x, y), ":", font, PROMPT_CMD)
    x = draw_text(draw, (x, y), "~/nasmhex", font, PROMPT_PATH)
    x = draw_text(draw, (x, y), "$ ", font, PROMPT_CMD)
    draw_text(draw, (x, y), "./nasmhex samples/hello.bin", font, PROMPT_CMD)
    y += line_h

    for raw in dump_lines:
        if len(raw) == 8 and all(c in "0123456789abcdef" for c in raw):
            draw_text(draw, (x0, y), raw, font, OFFSET)
            y += line_h
            continue
        # offset(8) + 2 spaces + hex area + " |" + ascii + "|"
        if len(raw) >= 10 and raw[8:10] == "  ":
            draw_text(draw, (x0, y), raw[:8], font, OFFSET)
            rest = raw[8:]
            pipe = rest.rfind("|")
            first_pipe = rest.find("|")
            if first_pipe != -1 and pipe != first_pipe:
                hex_part = rest[: first_pipe]
                ascii_part = rest[first_pipe : pipe + 1]
                x = draw_text(draw, (x0 + draw.textbbox((0, 0), raw[:8], font=font)[2], y), hex_part, font, HEX)
                # color ascii inside pipes
                draw_text(draw, (x, y), ascii_part, font, ASCII)
            else:
                draw_text(draw, (x0, y), raw, font, HEX)
        else:
            draw_text(draw, (x0, y), raw, font, HEX)
        y += line_h

    # block cursor after the last line
    draw.rectangle((x0, y + 2, x0 + 8, y + 16), fill=CURSOR)

    img.save(OUT, "PNG")
    print("wrote", OUT, img.size)


if __name__ == "__main__":
    main()
