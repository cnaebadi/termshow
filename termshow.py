import argparse
import curses
import re
import subprocess
import time

# 5x7 glyphs, top bit on the left. Lowercase is drawn as uppercase.
FONT = {
    "A": [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    "B": [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    "C": [0b01111, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b01111],
    "D": [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
    "E": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    "F": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
    "G": [0b01111, 0b10000, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111],
    "H": [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    "I": [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b11111],
    "J": [0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100],
    "K": [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
    "L": [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    "M": [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
    "N": [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
    "O": [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    "P": [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    "Q": [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
    "R": [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    "S": [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
    "T": [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    "U": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    "V": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
    "W": [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010],
    "X": [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001],
    "Y": [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    "Z": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
    "0": [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
    "1": [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    "2": [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111],
    "3": [0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110],
    "4": [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    "5": [0b11111, 0b10000, 0b10000, 0b11110, 0b00001, 0b00001, 0b11110],
    "6": [0b01110, 0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    "7": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    "8": [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    "9": [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001, 0b01110],
    " ": [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
    "!": [0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100],
    "?": [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b00000, 0b00100],
    ".": [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b01100, 0b01100],
    ",": [0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00100, 0b01000],
    ":": [0b00000, 0b00100, 0b00100, 0b00000, 0b00100, 0b00100, 0b00000],
    ";": [0b00000, 0b00100, 0b00100, 0b00000, 0b00100, 0b00100, 0b01000],
    "-": [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000],
    "'": [0b00100, 0b00100, 0b01000, 0b00000, 0b00000, 0b00000, 0b00000],
    '"': [0b01010, 0b01010, 0b10100, 0b00000, 0b00000, 0b00000, 0b00000],
    "(": [0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010],
    ")": [0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000],
    "/": [0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000],
    "+": [0b00000, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0b00000],
    "=": [0b00000, 0b00000, 0b11111, 0b00000, 0b11111, 0b00000, 0b00000],
    "@": [0b01110, 0b10001, 0b10111, 0b10101, 0b10111, 0b10000, 0b01110],
    "#": [0b01010, 0b01010, 0b11111, 0b01010, 0b11111, 0b01010, 0b01010],
}

HEADER_SCALE = {"h1": 4, "h2": 3, "h3": 2, "h4": 1}
HEADER_RANK = {"h1": 4, "h2": 3, "h3": 2, "h4": 1}
HEADER_COLOR = {"h1": 1, "h2": 2, "h3": 3, "h4": 4}
NAMED_STYLE = re.compile(r"^(h[1-4]|bold|normal)\s*:\s*(.*)$", re.IGNORECASE)
MARKDOWN_HEADER = re.compile(r"^(#{1,4})\s+(.*)$")
HAS_COLOR = False


def normalize_text(text):
    return (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2026", "...")
    )


def glyph_for(ch):
    if ch == " ":
        return " "
    ch = ch.upper() if ch.isalpha() else ch
    return FONT.get(ch)


def can_draw_header(text):
    text = normalize_text(text).replace("**", "")
    return bool(text.strip()) and all(glyph_for(ch) is not None for ch in text)


def header_width(text, scale):
    text = normalize_text(text).replace("**", "")
    width = 0
    prev_space = True
    for ch in text:
        if ch == " ":
            width += scale * 2
            prev_space = True
            continue
        if not prev_space:
            width += scale
        width += 5 * scale
        prev_space = False
    return width


TYPE_DELAY = 0.05


def render_header_rows(text, scale):
    text = normalize_text(text).replace("**", "")
    height = 7 * scale
    pieces = []
    prev_space = True
    for ch in text:
        if ch == " ":
            pieces.append({"rows": [" " * (scale * 2)] * height, "pause": True})
            prev_space = True
            continue
        glyph = glyph_for(ch)
        if glyph is None:
            return None
        if not prev_space:
            pieces.append({"rows": [" " * scale] * height, "pause": False})
        piece = []
        for bits in glyph:
            segment = ""
            for bit in range(5):
                on = (bits >> (4 - bit)) & 1
                segment += ("█" if on else " ") * scale
            piece.extend([segment] * scale)
        pieces.append({"rows": piece, "pause": True})
        prev_space = False
    trim_header_pieces(pieces)
    rows = join_header_pieces(pieces, height)
    return rows, pieces


def trim_header_pieces(pieces):
    while pieces:
        rows = pieces[-1]["rows"]
        if not rows or not rows[0]:
            pieces.pop()
            continue
        if not all(row.endswith(" ") for row in rows):
            break
        pieces[-1]["rows"] = [row[:-1] for row in rows]


def join_header_pieces(pieces, height):
    if not pieces:
        return [""] * height
    return ["".join(piece["rows"][row] for piece in pieces) for row in range(height)]


def parse_spans(text):
    spans = []
    normal = []

    def flush():
        if normal:
            spans.append(("normal", "".join(normal)))
            normal.clear()

    i = 0
    while i < len(text):
        if text.startswith("**", i):
            end = text.find("**", i + 2)
            if end != -1:
                flush()
                spans.append(("bold", text[i + 2 : end]))
                i = end + 2
                continue
        normal.append(text[i])
        i += 1
    flush()
    return spans or [("normal", "")]


def parse_content_line(line, align):
    raw = line.rstrip("\n")
    if raw.strip() == "":
        return ("blank",)
    probe = raw.strip()
    named = NAMED_STYLE.match(probe)
    if named:
        style = named.group(1).lower()
        body = named.group(2).strip()
        if style in HEADER_SCALE:
            return ("header", style, body)
        return ("text", [(style, body)])
    markdown = MARKDOWN_HEADER.match(probe)
    if markdown:
        return ("header", "h" + str(len(markdown.group(1))), markdown.group(2).strip())
    body = raw if align == "left" else raw.strip()
    return ("text", parse_spans(body))


def parse_slide_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.read().split("\n")

    slides = []
    current = {"type": "text", "align": "center", "content": []}

    for line in lines:
        if line.strip().startswith(":::"):
            if current["content"]:
                slides.append(current)
            current = slide_from_header(line)
        else:
            current["content"].append(line)
    if current["content"]:
        slides.append(current)
    return slides


def slide_from_header(line):
    tokens = line.strip()[3:].split()
    slide_type = tokens[0] if tokens else "text"
    align = "center"
    for token in tokens[1:]:
        if token in ("left", "center"):
            align = token
    return {"type": slide_type, "align": align, "content": []}


def fit_header_scales(items, max_w, max_h):
    scales = []
    for item in items:
        if item[0] != "header" or not can_draw_header(item[2]):
            scales.append(None)
            continue
        scale = HEADER_SCALE[item[1]]
        while scale > 1 and (
            header_width(item[2], scale) > max_w or 7 * scale > max_h
        ):
            scale -= 1
        if header_width(item[2], scale) > max_w or 7 * scale > max_h:
            scales.append(None)
        else:
            scales.append(scale)

    def height(current):
        total = 0
        for index, (item, scale) in enumerate(zip(items, current)):
            if item[0] == "header" and scale:
                total += 7 * scale
                if index != len(items) - 1:
                    total += 1
            else:
                total += 1
        return total

    def enforce_hierarchy():
        higher_scale = None
        for rank in (4, 3, 2, 1):
            indexes = [
                i
                for i, item in enumerate(items)
                if item[0] == "header" and item[1] in HEADER_RANK and HEADER_RANK[item[1]] == rank and scales[i]
            ]
            if not indexes:
                continue
            if higher_scale is not None:
                for i in indexes:
                    if scales[i] >= higher_scale:
                        scales[i] = higher_scale - 1
                    if scales[i] is not None and scales[i] < 1:
                        scales[i] = None
            kept = [scales[i] for i in indexes if scales[i]]
            if kept:
                smallest = min(kept)
                higher_scale = smallest if higher_scale is None else min(higher_scale, smallest)

    enforce_hierarchy()
    while height(scales) > max_h:
        shrinkable = [i for i, scale in enumerate(scales) if scale and scale > 1]
        if shrinkable:
            chosen = min(shrinkable, key=lambda i: (HEADER_RANK[items[i][1]], -scales[i]))
            scales[chosen] -= 1
            enforce_hierarchy()
            continue
        collapsible = [i for i, scale in enumerate(scales) if scale == 1]
        if not collapsible:
            break
        chosen = min(collapsible, key=lambda i: HEADER_RANK[items[i][1]])
        scales[chosen] = None
        enforce_hierarchy()
    enforce_hierarchy()
    return scales


def layout_lines(content, align, max_w, max_h):
    lines = list(content)
    if align == "center":
        while lines and lines[0].strip() == "":
            lines.pop(0)
        while lines and lines[-1].strip() == "":
            lines.pop()

    items = [parse_content_line(line, align) for line in lines]
    scales = fit_header_scales(items, max_w, max_h)
    blocks = []
    for index, (item, scale) in enumerate(zip(items, scales)):
        if item[0] == "blank":
            blocks.append({"kind": "plain", "style": "normal", "rows": [""]})
        elif item[0] == "header":
            rendered = render_header_rows(item[2], scale) if scale else None
            if rendered:
                rows, pieces = rendered
                blocks.append({"kind": "header", "style": item[1], "rows": rows, "pieces": pieces})
                if index != len(items) - 1:
                    blocks.append({"kind": "gap", "style": "normal", "rows": [""]})
            else:
                blocks.append({"kind": "fallback", "style": item[1], "rows": [item[2]]})
        else:
            blocks.append({"kind": "spans", "style": None, "rows": [item[1]]})
    return blocks


def block_height(blocks):
    return sum(len(block["rows"]) for block in blocks)


def span_width(spans):
    return sum(len(text) for _, text in spans)


def style_attr(style, fallback=False):
    attr = curses.A_NORMAL if style == "normal" else curses.A_BOLD
    if fallback and style in ("h1", "h2"):
        attr |= curses.A_UNDERLINE
    color = HEADER_COLOR.get(style)
    if HAS_COLOR and color:
        attr |= curses.color_pair(color)
    return attr


def safe_add(stdscr, y, x, text, attr=0):
    rows, cols = stdscr.getmaxyx()
    if y < 0 or y >= rows or not text or x >= cols:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    limit = cols - x
    if y == rows - 1:
        limit -= 1
    text = text[:limit]
    if not text:
        return
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def line_x(align, cols, width, left_pad):
    if align == "center":
        return max(0, (cols - width) // 2)
    return left_pad


def pause_type(stdscr):
    stdscr.refresh()
    time.sleep(TYPE_DELAY)


def draw_typed_text(stdscr, y, x, text, attr, typewriter):
    if not typewriter:
        safe_add(stdscr, y, x, text, attr)
        return
    for ch in text:
        safe_add(stdscr, y, x, ch, attr)
        x += 1
        pause_type(stdscr)


def draw_header_pieces(stdscr, y, x, pieces, attr, typewriter):
    rows, _cols = stdscr.getmaxyx()
    for piece in pieces:
        for dy, row in enumerate(piece["rows"]):
            if y + dy >= rows - 1:
                break
            safe_add(stdscr, y + dy, x, row, attr)
        x += len(piece["rows"][0]) if piece["rows"] else 0
        if typewriter and piece["pause"]:
            pause_type(stdscr)


def draw_blocks(stdscr, blocks, align, top, typewriter, left_pad):
    rows, cols = stdscr.getmaxyx()
    height = block_height(blocks)
    usable = max(1, (rows - 2) - top + 1)
    y = top + max(0, (usable - height) // 2) if align == "center" else top

    for block in blocks:
        if y >= rows - 1:
            break
        attr = style_attr(block["style"] or "normal", fallback=block["kind"] == "fallback")
        if block["kind"] == "spans":
            spans = block["rows"][0]
            x = line_x(align, cols, span_width(spans), left_pad)
            for style, text in spans:
                draw_typed_text(stdscr, y, x, text, style_attr(style), typewriter)
                x += len(text)
            y += 1
            continue

        if block["kind"] == "header" and block.get("pieces"):
            width = max((len(row) for row in block["rows"]), default=0)
            x = line_x(align, cols, width, left_pad)
            draw_header_pieces(stdscr, y, x, block["pieces"], attr, typewriter)
            y += len(block["rows"])
            continue

        if block["kind"] == "fallback":
            text = block["rows"][0] if block["rows"] else ""
            x = line_x(align, cols, len(text), left_pad)
            draw_typed_text(stdscr, y, x, text, attr, typewriter)
            y += 1
            continue

        for row in block["rows"]:
            if y >= rows - 1:
                break
            width = len(row)
            x = line_x(align, cols, width, left_pad)
            safe_add(stdscr, y, x, row, attr)
            y += 1


def render_art(slide):
    rendered = []
    for line in slide["content"]:
        if not line.strip():
            continue
        try:
            output = subprocess.check_output(line, shell=True, text=True)
            rendered.extend(output.splitlines() or [""])
        except subprocess.CalledProcessError as exc:
            rendered.append("[!] Command failed: " + line)
            rendered.append(str(exc))
    return [{"kind": "plain", "style": "normal", "rows": [row]} for row in rendered]


def render_slide(stdscr, slide, index, total, show_page, typewriter):
    stdscr.erase()
    rows, cols = stdscr.getmaxyx()
    if show_page:
        safe_add(stdscr, 0, 0, "██ {}/{}".format(index + 1, total))

    align = slide.get("align", "center")
    top = 2 if show_page else 1
    max_h = max(1, (rows - 2) - top + 1)
    max_w = max(1, cols - 2)
    left_pad = 2 if slide["type"] == "options" and align == "left" else 0

    if slide["type"] == "art":
        blocks = render_art(slide)
    else:
        blocks = layout_lines(slide["content"], align, max_w, max_h)

    draw_blocks(stdscr, blocks, align, top, typewriter and slide["type"] != "art", left_pad)

    hint = "↑/↓ navigate    a auto    q quit"
    safe_add(stdscr, rows - 1, max(0, (cols - len(hint)) // 2), hint, curses.A_DIM)
    stdscr.refresh()


def prompt_delay(stdscr):
    rows, cols = stdscr.getmaxyx()
    prompt = "Auto-play delay in seconds (0-1000): "
    y = max(0, rows - 2)
    curses.echo()
    curses.curs_set(1)
    try:
        stdscr.move(y, 0)
        stdscr.clrtoeol()
        stdscr.addstr(y, 0, prompt[: cols - 1])
        stdscr.refresh()
        input_str = stdscr.getstr().decode("utf-8")
    except curses.error:
        input_str = ""
    curses.noecho()
    curses.curs_set(0)
    try:
        value = int(input_str.strip())
        if 0 <= value <= 1000:
            return value
    except ValueError:
        pass
    return None


def init_colors():
    global HAS_COLOR
    HAS_COLOR = False
    if not curses.has_colors():
        return
    try:
        curses.start_color()
        curses.use_default_colors()
        palette = [
            (1, curses.COLOR_YELLOW),
            (2, curses.COLOR_CYAN),
            (3, curses.COLOR_GREEN),
            (4, curses.COLOR_MAGENTA),
        ]
        for number, fg in palette:
            curses.init_pair(number, fg, -1)
        HAS_COLOR = True
    except curses.error:
        HAS_COLOR = False


def slideshow(stdscr, slides, show_page, typewriter):
    curses.curs_set(0)
    stdscr.keypad(True)
    init_colors()

    index = 0
    total = len(slides)
    auto_mode = False
    delay = 3

    stdscr.nodelay(False)
    render_slide(stdscr, slides[index], index, total, show_page, typewriter)

    while True:
        key = stdscr.getch()

        if key == curses.KEY_UP:
            if index > 0:
                index -= 1
                render_slide(stdscr, slides[index], index, total, show_page, typewriter)

        elif key == curses.KEY_DOWN:
            if index < total - 1:
                index += 1
                render_slide(stdscr, slides[index], index, total, show_page, typewriter)

        elif key == ord("q"):
            break

        elif key == ord("a"):
            chosen = prompt_delay(stdscr)
            if chosen is not None:
                delay = chosen
                auto_mode = True
                stdscr.nodelay(True)
                render_slide(stdscr, slides[index], index, total, show_page, False)
            else:
                render_slide(stdscr, slides[index], index, total, show_page, False)
                rows, cols = stdscr.getmaxyx()
                safe_add(stdscr, max(0, rows - 2), 0, "Invalid input. Press any key to continue."[: cols - 1])
                stdscr.refresh()
                stdscr.nodelay(False)
                stdscr.getch()
                render_slide(stdscr, slides[index], index, total, show_page, False)

        if auto_mode:
            time.sleep(delay)
            if index < total - 1:
                index += 1
                render_slide(stdscr, slides[index], index, total, show_page, False)
            else:
                auto_mode = False
                stdscr.nodelay(False)


def main():
    parser = argparse.ArgumentParser(description="Terminal slideshow with curses")
    parser.add_argument("file", help="Path to slide file")
    parser.add_argument("--no-page-number", action="store_true", help="Hide slide number display")
    parser.add_argument("-t", action="store_true", help="Show slide text with typewriter effect")
    args = parser.parse_args()

    slides = parse_slide_file(args.file)
    if not slides:
        raise SystemExit("No slides found in {}".format(args.file))
    curses.wrapper(slideshow, slides, not args.no_page_number, args.t)


if __name__ == "__main__":
    main()
