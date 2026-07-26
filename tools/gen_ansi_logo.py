"""
Генератор ANSI-баннера Cardinal: assets/logo_source.png -> assets/logo.ans.

Картинка переводится в символьную «пиксель-графику» (рампа символов по яркости,
256-цветные ANSI-коды) в палитре Playerok: чёрный -> тёмно-синий -> синий -> белый.
Справа от статуи — надпись PLAYEROK/CARDINAL полублочным шрифтом и подписи
(вертикально по центру). Готовый арт печатает banner() в cardinal.sh
(простой `cat assets/logo.ans`).

Запуск (нужен Pillow): python tools/gen_ansi_logo.py
"""
from __future__ import annotations

import pathlib

from PIL import Image, ImageFilter, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "logo_source.png"
TARGET = ROOT / "assets" / "logo.ans"

WIDTH = 78          # колонок — влезает в терминал 80x24
CHAR_ASPECT = 0.46  # символ терминала примерно вдвое выше своей ширины

#: Рампа символов по возрастанию яркости (тёмное -> светлое).
RAMP = " .'`,:;!i>~+_-?][}{1)(|tfjrxnuvczXYUJCLQ0OZ#MW&8%B@$"

#: Яркость -> цвет xterm-256: чёрный -> тёмно-синие -> синие -> голубые -> белый.
PALETTE = [(16, 233), (34, 17), (55, 18), (76, 19), (97, 20), (118, 25), (139, 26),
           (160, 27), (180, 33), (200, 39), (220, 75), (238, 117), (256, 15)]

GAP = 2  # колонок между статуей и надписью

_CYAN = "\x1b[38;5;51m"
_RED = "\x1b[38;5;196m"
_GREY = "\x1b[38;5;245m"
_RESET = "\x1b[0m"

#: Текстовый блок справа от статуи: (цветной текст, видимая ширина).
SIDE_TEXT: list[tuple[str, int]] = [
    (f"{_CYAN}█▀█ █   ▄▀█ █▄█ █▀▀ █▀█ █▀█ █▄▀{_RESET}", 31),
    (f"{_CYAN}█▀▀ █▄▄ █▀█  █  ██▄ █▀▄ █▄█ █ █{_RESET}", 31),
    ("", 0),
    (f"{_RED}█▀▀ ▄▀█ █▀█ █▀▄ █ █▄ █ ▄▀█ █{_RESET}", 28),
    (f"{_RED}█▄▄ █▀█ █▀▄ █▄▀ █ █ ▀█ █▀█ █▄▄{_RESET}", 30),
    ("", 0),
    (f"{_GREY}бот-комбайн для продавцов Playerok{_RESET}", 34),
    (f"{_GREY}· /menu в Telegram{_RESET}", 18),
    (f"{_GREY}Создатель:{_RESET} {_CYAN}https://t.me/Scwee_xz{_RESET}", 32),
]


def _tone_curve(p: int) -> int:
    """S-кривая: глушит фоновый «город», вытягивает статую и кольцо."""
    if p < 38:
        return int(p * 0.45)
    return min(255, int(255 * ((p - 38) / 217) ** 0.66))


def _color_for(lum: int) -> int:
    for threshold, color in PALETTE:
        if lum < threshold:
            return color
    return 15


def render() -> str:
    im = Image.open(SOURCE).convert("L")
    w, h = im.size
    im = im.crop((int(w * 0.06), int(h * 0.02), int(w * 0.94), int(h * 0.98)))
    im = ImageOps.autocontrast(im, cutoff=1)
    im = im.point(_tone_curve)
    # Дилатация: тонкие яркие линии (кольцо, лучи короны) переживают уменьшение.
    im = im.filter(ImageFilter.MaxFilter(5))
    w, h = im.size
    rows = max(1, round(h / w * WIDTH * CHAR_ASPECT))
    im = im.resize((WIDTH, rows), Image.LANCZOS)

    lines = []
    for y in range(rows):
        parts: list[str] = []
        prev_color = None
        for x in range(WIDTH):
            lum = im.getpixel((x, y))
            if lum < 8:
                parts.append(" ")
                prev_color = None
                continue
            # Совсем тёмные места — спокойное «зерно» из точек, как в референсе.
            char = "." if lum < 26 else RAMP[min(len(RAMP) - 1, lum * len(RAMP) // 256)]
            color = _color_for(lum)
            if color != prev_color:
                parts.append(f"\x1b[38;5;{color}m")
                prev_color = color
            parts.append(char)
        parts.append("\x1b[0m")
        lines.append("".join(parts))
    return _attach_side_text(lines)


def _attach_side_text(lines: list[str]) -> str:
    """Пристраивает надпись/подписи справа от статуи, вертикально по центру."""
    start = max(0, (len(lines) - len(SIDE_TEXT)) // 2)
    for offset, (text, width) in enumerate(SIDE_TEXT):
        if not text:
            continue
        row = start + offset
        if row >= len(lines):
            break
        # Каждая строка статуи ровно WIDTH видимых символов — просто дописываем хвост.
        lines[row] += " " * GAP + text
    return "\n".join(lines) + "\n"


def main() -> None:
    art = render()
    TARGET.write_text(art, encoding="utf-8")
    print(f"OK: {TARGET} ({art.count(chr(10))} строк, {len(art)} байт)")


if __name__ == "__main__":
    main()
