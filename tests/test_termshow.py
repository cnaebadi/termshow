import curses
import runpy
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import termshow

ROOT = Path(__file__).resolve().parents[1]


class FakeScreen:
    def __init__(self, rows=24, cols=80, keys=None, inputs=None):
        self.rows = rows
        self.cols = cols
        self.keys = list(keys or [])
        self.inputs = list(inputs or [])
        self.cells = {}
        self.log = []
        self.nodelay_flag = None
        self.fail_add = False
        self.fail_input = False

    def getmaxyx(self):
        return self.rows, self.cols

    def erase(self):
        self.cells = {}

    def addstr(self, y, x, text, attr=0):
        if self.fail_add:
            raise curses.error("addstr")
        self.log.append((y, x, text, attr))
        row = self.cells.setdefault(y, {})
        for offset, ch in enumerate(text):
            row[x + offset] = (ch, attr)

    def refresh(self):
        return None

    def keypad(self, _flag):
        return None

    def nodelay(self, flag):
        self.nodelay_flag = flag

    def getch(self):
        if self.keys:
            return self.keys.pop(0)
        return -1

    def move(self, _y, _x):
        if self.fail_input:
            raise curses.error("move")

    def clrtoeol(self):
        return None

    def getstr(self):
        if self.fail_input:
            raise curses.error("getstr")
        if not self.inputs:
            return b""
        return self.inputs.pop(0)


def painted(screen):
    lines = []
    for y in range(screen.rows):
        row = screen.cells.get(y, {})
        if not row:
            lines.append("")
            continue
        last = max(row)
        lines.append("".join(row.get(x, (" ", 0))[0] for x in range(last + 1)).rstrip())
    return "\n".join(lines)


def find_char(screen, ch):
    for y, row in screen.cells.items():
        for x, (glyph, attr) in row.items():
            if glyph == ch:
                return y, x, attr
    return None


class TermShowTests(unittest.TestCase):
    def setUp(self):
        self._color = termshow.HAS_COLOR

    def tearDown(self):
        termshow.HAS_COLOR = self._color

    def test_glyph_lookup_and_width(self):
        self.assertEqual(termshow.glyph_for(" "), " ")
        self.assertEqual(termshow.glyph_for("z"), termshow.FONT["Z"])
        self.assertEqual(termshow.glyph_for("9"), termshow.FONT["9"])
        self.assertIsNone(termshow.glyph_for("_"))
        self.assertEqual(termshow.header_width("AB", 2), 22)
        self.assertEqual(termshow.header_width("A B", 2), 24)
        self.assertFalse(termshow.can_draw_header("  "))
        self.assertFalse(termshow.can_draw_header("**"))
        self.assertTrue(termshow.can_draw_header("**A**"))
        self.assertFalse(termshow.can_draw_header("A_B"))
        self.assertTrue(termshow.can_draw_header("A\u2014B\u2026"))

    def test_every_font_character_renders(self):
        for ch in termshow.FONT:
            if ch == " ":
                continue
            source = ch.lower() if ch.isalpha() else ch
            rendered = termshow.render_header_rows(source, 1)
            self.assertIsNotNone(rendered)
            rows, pieces = rendered
            self.assertEqual(rows, termshow.join_header_pieces(pieces, 7))
            self.assertTrue(any("█" in row for row in rows))

        self.assertIsNone(termshow.render_header_rows("A_B", 1))
        rows, pieces = termshow.render_header_rows("   ", 1)
        self.assertEqual(pieces, [])
        self.assertEqual(rows, [""] * 7)

        plain, _plain_pieces = termshow.render_header_rows("A", 1)
        spaced, _spaced_pieces = termshow.render_header_rows("A ", 1)
        self.assertEqual(plain, spaced)
        wide, wide_pieces = termshow.render_header_rows("A B", 2)
        self.assertEqual(len(wide), 14)
        self.assertEqual([piece["pause"] for piece in wide_pieces], [True, True, True])
        letters, letter_pieces = termshow.render_header_rows("AB", 1)
        self.assertEqual([piece["pause"] for piece in letter_pieces], [True, False, True])
        self.assertTrue(any("█" in row for row in letters))

        curly, _pieces = termshow.render_header_rows("It\u2019s", 1)
        straight, _straight_pieces = termshow.render_header_rows("It's", 1)
        self.assertEqual(curly, straight)

    def test_trim_and_join_edges(self):
        pieces = [{"rows": [], "pause": True}]
        termshow.trim_header_pieces(pieces)
        self.assertEqual(pieces, [])
        self.assertEqual(termshow.join_header_pieces([], 3), ["", "", ""])

    def test_parse_spans_and_lines(self):
        self.assertEqual(termshow.parse_spans(""), [("normal", "")])
        self.assertEqual(termshow.parse_spans("plain"), [("normal", "plain")])
        self.assertEqual(
            termshow.parse_spans("a **b** c"),
            [("normal", "a "), ("bold", "b"), ("normal", " c")],
        )
        self.assertEqual(termshow.parse_spans("**start**"), [("bold", "start")])
        self.assertEqual(termshow.parse_spans("open **"), [("normal", "open **")])

        self.assertEqual(termshow.parse_content_line("   ", "center"), ("blank",))
        self.assertEqual(termshow.parse_content_line("H1: Hello", "center"), ("header", "h1", "Hello"))
        self.assertEqual(termshow.parse_content_line("bold: Hi", "center"), ("text", [("bold", "Hi")]))
        self.assertEqual(termshow.parse_content_line("normal: Hi", "left"), ("text", [("normal", "Hi")]))
        self.assertEqual(termshow.parse_content_line("###  Zoom", "center"), ("header", "h3", "Zoom"))
        self.assertEqual(termshow.parse_content_line("# Title", "center"), ("header", "h1", "Title"))
        self.assertEqual(termshow.parse_content_line("## Title", "center"), ("header", "h2", "Title"))
        self.assertEqual(termshow.parse_content_line("#### Title", "center"), ("header", "h4", "Title"))
        self.assertEqual(termshow.parse_content_line("##### Title", "center")[0], "text")
        self.assertEqual(
            termshow.parse_content_line("  indented", "left"),
            ("text", [("normal", "  indented")]),
        )
        self.assertEqual(
            termshow.parse_content_line("  indented", "center"),
            ("text", [("normal", "indented")]),
        )

    def test_parse_slide_file(self):
        with self.temporary_slide(
            "intro\n"
            "::: \n"
            "hello\n"
            "::: art left extra\n"
            "cmd\n"
            "::: options center\n"
            "::: text left center\n"
            "last\n"
        ) as path:
            slides = termshow.parse_slide_file(str(path))
        self.assertEqual([slide["type"] for slide in slides], ["text", "text", "art", "text"])
        self.assertEqual(slides[0]["content"], ["intro"])
        self.assertEqual(slides[1]["align"], "center")
        self.assertEqual(slides[1]["content"], ["hello"])
        self.assertEqual(slides[2]["align"], "left")
        self.assertEqual(slides[2]["type"], "art")
        self.assertEqual(slides[3]["align"], "center")
        self.assertEqual(termshow.slide_from_header("::: options center left")["align"], "left")

        with self.temporary_slide("::: text\n::: art") as empty:
            self.assertEqual(termshow.parse_slide_file(str(empty)), [])

        demo = termshow.parse_slide_file(str(ROOT / "slides" / "demo.slide"))
        self.assertEqual([slide["type"] for slide in demo], ["text", "text", "art", "options"])
        self.assertEqual([slide["align"] for slide in demo], ["center", "left", "center", "center"])

    def test_header_scales_fit_shrink_and_drop(self):
        self.assertEqual(
            termshow.fit_header_scales([("header", "h1", "A"), ("header", "h2", "A")], 200, 40),
            [4, 1],
        )
        self.assertEqual(
            termshow.fit_header_scales([("header", "h2", "A"), ("header", "h1", "A")], 80, 8),
            [None, 1],
        )
        self.assertEqual(
            termshow.fit_header_scales(
                [
                    ("header", "h4", "A"),
                    ("text", [("normal", "x")]),
                    ("text", [("normal", "y")]),
                    ("text", [("normal", "z")]),
                ],
                80,
                8,
            ),
            [None, None, None, None],
        )
        self.assertEqual(
            termshow.fit_header_scales([("text", [("normal", "x")])] * 5, 80, 2),
            [None] * 5,
        )
        self.assertEqual(termshow.fit_header_scales([("header", "h1", "HELLO")], 10, 40), [None])
        self.assertEqual(termshow.fit_header_scales([("header", "h1", "A")], 40, 5), [None])
        self.assertEqual(termshow.fit_header_scales([("header", "h1", "HELLO")], 40, 40), [1])
        self.assertEqual(
            termshow.fit_header_scales(
                [("blank",), ("text", [("normal", "hi")]), ("header", "h1", "سلام")],
                80,
                20,
            ),
            [None, None, None],
        )

    def test_layout_lines(self):
        self.assertEqual(
            [block["kind"] for block in termshow.layout_lines(["", "h1: A", ""], "center", 80, 40)],
            ["header"],
        )
        self.assertEqual(
            [block["kind"] for block in termshow.layout_lines(["", "h1: A", ""], "left", 80, 40)],
            ["plain", "header", "gap", "plain"],
        )
        mixed = termshow.layout_lines(["h1: A", "", "say **hi**"], "center", 80, 40)
        self.assertEqual([block["kind"] for block in mixed], ["header", "gap", "plain", "spans"])
        fallback = termshow.layout_lines(["h1: سلام", "h1:"], "center", 40, 10)
        self.assertEqual([block["kind"] for block in fallback], ["fallback", "fallback"])
        self.assertEqual(termshow.layout_lines([], "center", 80, 20), [])
        self.assertEqual(termshow.block_height(mixed), sum(len(block["rows"]) for block in mixed))
        self.assertEqual(termshow.span_width([("normal", "ab"), ("bold", "c")]), 3)

    def test_style_attr(self):
        termshow.HAS_COLOR = False
        self.assertEqual(termshow.style_attr("normal"), curses.A_NORMAL)
        self.assertTrue(termshow.style_attr("bold") & curses.A_BOLD)
        self.assertTrue(termshow.style_attr("h1", fallback=True) & curses.A_UNDERLINE)
        self.assertFalse(termshow.style_attr("h3", fallback=True) & curses.A_UNDERLINE)

        seen = []

        def color_pair(number):
            seen.append(number)
            return 0

        with patch.object(termshow.curses, "color_pair", color_pair):
            termshow.HAS_COLOR = True
            termshow.style_attr("h2")
            termshow.style_attr("bold")
            termshow.style_attr("normal")
        self.assertEqual(seen, [2])

    def test_safe_add_clips_and_swallows_errors(self):
        screen = FakeScreen(4, 6)
        termshow.safe_add(screen, -1, 0, "X")
        termshow.safe_add(screen, 4, 0, "X")
        termshow.safe_add(screen, 0, 0, "")
        termshow.safe_add(screen, 0, 6, "X")
        termshow.safe_add(screen, 1, -3, "HELLO")
        termshow.safe_add(screen, 1, -100, "HI")
        termshow.safe_add(screen, 3, 0, "HELLO!!")
        termshow.safe_add(screen, 3, 4, "HELLO")
        self.assertEqual(screen.cells[1][0][0], "L")
        self.assertIn((3, 0, "HELLO", 0), screen.log)
        self.assertIn((3, 4, "H", 0), screen.log)

        screen.fail_add = True
        termshow.safe_add(screen, 0, 0, "boom")

    def test_line_positions_and_draw_edges(self):
        with patch.object(termshow.time, "sleep", lambda _delay: None):
            self.assertEqual(termshow.line_x("center", 10, 4, 2), 3)
            self.assertEqual(termshow.line_x("center", 10, 40, 2), 0)
            self.assertEqual(termshow.line_x("left", 10, 4, 2), 2)

            screen = FakeScreen(6, 20)
            termshow.draw_blocks(
                screen,
                [
                    {"kind": "plain", "style": "normal", "rows": ["a", "b", "c", "d", "e", "f"]},
                    {"kind": "spans", "style": None, "rows": [[("normal", "NO")]]},
                ],
                "left",
                0,
                False,
                0,
            )
            self.assertNotIn("NO", painted(screen))

            termshow.draw_header_pieces(
                screen,
                5,
                0,
                [{"rows": ["AB", "CD"], "pause": True}],
                0,
                False,
            )
            termshow.draw_header_pieces(
                screen,
                1,
                1,
                [{"rows": [], "pause": True}, {"rows": ["X"], "pause": False}],
                0,
                True,
            )
            termshow.draw_blocks(
                screen,
                [
                    {"kind": "header", "style": "h3", "rows": ["ZZ"]},
                    {
                        "kind": "header",
                        "style": "h1",
                        "rows": [],
                        "pieces": [{"rows": ["Q"], "pause": False}],
                    },
                    {"kind": "fallback", "style": "h2", "rows": []},
                    {"kind": "fallback", "style": "h1", "rows": ["Hey"]},
                ],
                "left",
                0,
                True,
                0,
            )
            self.assertTrue(find_char(screen, "H")[2] & curses.A_UNDERLINE)
            self.assertIn("Hey", painted(screen))

    def test_render_centers_styles_and_types(self):
        slept = []
        with patch.object(termshow.time, "sleep", lambda delay: slept.append(delay)), patch.object(
            termshow.curses, "color_pair", lambda number: number
        ):
            centered = FakeScreen(20, 40)
            termshow.render_slide(
                centered,
                {"type": "text", "align": "center", "content": ["Hi"]},
                0,
                3,
                True,
                False,
            )
            self.assertEqual(find_char(centered, "H")[:2], (10, 19))
            self.assertTrue(painted(centered).splitlines()[0].startswith("██ 1/3"))

            left = FakeScreen(20, 40)
            termshow.render_slide(
                left,
                {"type": "options", "align": "left", "content": ["Go"]},
                1,
                3,
                False,
                False,
            )
            self.assertEqual(find_char(left, "G")[:2], (1, 2))
            self.assertNotIn("██", painted(left))

            options = FakeScreen(12, 30)
            termshow.render_slide(
                options,
                {"type": "options", "align": "center", "content": ["Go"]},
                0,
                1,
                False,
                False,
            )
            self.assertGreater(find_char(options, "G")[1], 2)

            implicit = FakeScreen(20, 40)
            termshow.render_slide(implicit, {"type": "text", "content": ["Hi"]}, 0, 1, False, False)
            self.assertGreater(find_char(implicit, "H")[1], 0)

            typed = FakeScreen(30, 80)
            slide = {"type": "text", "align": "left", "content": ["h4: HI", "Say **hi**", "h1: سلام"]}
            termshow.HAS_COLOR = True
            termshow.render_slide(typed, slide, 0, 1, False, True)
            instant = FakeScreen(30, 80)
            termshow.render_slide(instant, slide, 0, 1, False, False)
            self.assertEqual(painted(typed), painted(instant))
            self.assertGreaterEqual(slept.count(termshow.TYPE_DELAY), 4)
            self.assertTrue(find_char(typed, "h")[2] & curses.A_BOLD)
            self.assertFalse(find_char(typed, "S")[2] & curses.A_BOLD)

            tiny = FakeScreen(1, 5)
            termshow.render_slide(
                tiny,
                {"type": "text", "align": "center", "content": ["Hello"]},
                0,
                1,
                True,
                False,
            )
            self.assertTrue(tiny.log)

    def test_render_art(self):
        def check_output(cmd, shell, text):
            self.assertTrue(shell)
            self.assertTrue(text)
            if cmd == "bad":
                raise subprocess.CalledProcessError(1, cmd)
            if cmd == "empty":
                return ""
            return "hello\nworld\n"

        with patch.object(termshow.subprocess, "check_output", check_output), patch.object(
            termshow.time, "sleep", lambda _delay: self.fail("art should not type")
        ):
            blocks = termshow.render_art({"content": ["", "  ", "empty", "bad", "figlet"]})
            rows = [block["rows"][0] for block in blocks]
            self.assertEqual(rows[0], "")
            self.assertTrue(rows[1].startswith("[!] Command failed: bad"))
            self.assertIn("hello", rows)
            self.assertIn("world", rows)

            screen = FakeScreen(20, 40)
            termshow.render_slide(
                screen,
                {"type": "art", "align": "center", "content": ["figlet"]},
                0,
                1,
                False,
                True,
            )
            self.assertGreater(find_char(screen, "h")[1], 0)

    def test_prompt_delay(self):
        with self.silent_curses():
            screen = FakeScreen(1, 8, inputs=[b"0", b"1000", b" 3 ", b"1001", b"-1", b"no", b""])
            self.assertEqual(termshow.prompt_delay(screen), 0)
            self.assertEqual(termshow.prompt_delay(screen), 1000)
            self.assertEqual(termshow.prompt_delay(screen), 3)
            self.assertIsNone(termshow.prompt_delay(screen))
            self.assertIsNone(termshow.prompt_delay(screen))
            self.assertIsNone(termshow.prompt_delay(screen))
            self.assertIsNone(termshow.prompt_delay(screen))

            screen.fail_input = True
            self.assertIsNone(termshow.prompt_delay(screen))

    def test_init_colors(self):
        termshow.HAS_COLOR = True
        with patch.object(termshow.curses, "has_colors", lambda: False):
            termshow.init_colors()
        self.assertFalse(termshow.HAS_COLOR)

        with patch.object(termshow.curses, "has_colors", lambda: True), patch.object(
            termshow.curses, "start_color", lambda: None
        ), patch.object(termshow.curses, "use_default_colors", lambda: None), patch.object(
            termshow.curses, "init_pair", lambda *_args: None
        ):
            termshow.init_colors()
        self.assertTrue(termshow.HAS_COLOR)

        def explode():
            raise curses.error("color")

        with patch.object(termshow.curses, "has_colors", lambda: True), patch.object(
            termshow.curses, "start_color", explode
        ):
            termshow.init_colors()
        self.assertFalse(termshow.HAS_COLOR)

    def test_slideshow_navigation_and_autoplay(self):
        slept = []
        slides = [
            {"type": "text", "align": "left", "content": ["zero"]},
            {"type": "text", "align": "left", "content": ["one"]},
            {"type": "text", "align": "left", "content": ["two"]},
        ]
        screen = FakeScreen(
            keys=[
                curses.KEY_UP,
                curses.KEY_DOWN,
                curses.KEY_DOWN,
                curses.KEY_DOWN,
                curses.KEY_UP,
                ord("a"),
                -1,
                ord("a"),
                ord("x"),
                ord("q"),
            ],
            inputs=[b"2", b"no"],
        )
        with self.silent_curses(), patch.object(termshow.time, "sleep", lambda delay: slept.append(delay)):
            termshow.slideshow(screen, slides, True, False)
        self.assertEqual(slept, [2, 2])
        self.assertFalse(screen.nodelay_flag)
        self.assertIn("two", painted(screen))
        self.assertTrue(any("Invalid input" in entry[2] for entry in screen.log))
        self.assertTrue(any(entry[2].startswith("██ 1/3") for entry in screen.log))
        self.assertTrue(any(entry[2].startswith("██ 3/3") for entry in screen.log))

    def test_slideshow_types_header_before_quit(self):
        slept = []
        screen = FakeScreen(keys=[ord("q")])
        with self.silent_curses(), patch.object(termshow.time, "sleep", lambda delay: slept.append(delay)):
            termshow.slideshow(
                screen,
                [{"type": "text", "align": "left", "content": ["h4: Ab"]}],
                False,
                True,
            )
        self.assertEqual(slept, [termshow.TYPE_DELAY, termshow.TYPE_DELAY])
        self.assertIn("█", painted(screen))

    def test_main_and_module_entrypoint(self):
        with self.temporary_slide("::: text\nHello\n") as deck:
            captured = {}

            def wrapper(_fn, slides, show_page, typewriter):
                captured["count"] = len(slides)
                captured["show_page"] = show_page
                captured["typewriter"] = typewriter

            with patch.object(termshow.curses, "wrapper", wrapper):
                with patch.object(sys, "argv", ["termshow", str(deck), "--no-page-number", "-t"]):
                    termshow.main()
                self.assertEqual(captured, {"count": 1, "show_page": False, "typewriter": True})

                with patch.object(sys, "argv", ["termshow", str(deck)]):
                    termshow.main()
                self.assertTrue(captured["show_page"])
                self.assertFalse(captured["typewriter"])

            with self.temporary_slide("::: text") as empty:
                with patch.object(sys, "argv", ["termshow", str(empty)]):
                    with self.assertRaises(SystemExit) as raised:
                        termshow.main()
            self.assertIn("No slides found", str(raised.exception))

            with patch.object(curses, "wrapper", lambda *_args: None), patch.object(
                sys, "argv", ["termshow", str(deck)]
            ):
                runpy.run_path(str(ROOT / "termshow.py"), run_name="__main__")

    def silent_curses(self):
        return ExitStackPatches(
            patch.object(termshow.curses, "echo", lambda: None),
            patch.object(termshow.curses, "noecho", lambda: None),
            patch.object(termshow.curses, "curs_set", lambda _n: None),
            patch.object(termshow.curses, "has_colors", lambda: False),
        )

    def temporary_slide(self, text):
        return TemporarySlide(text)


class ExitStackPatches:
    def __init__(self, *patches):
        self.patches = patches

    def __enter__(self):
        for item in self.patches:
            item.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        for item in reversed(self.patches):
            item.stop()
        return False


class TemporarySlide:
    def __init__(self, text):
        self.text = text
        self.path = None

    def __enter__(self):
        import tempfile

        handle = tempfile.NamedTemporaryFile("w", suffix=".slide", encoding="utf-8", delete=False)
        handle.write(self.text)
        handle.close()
        self.path = Path(handle.name)
        return self.path

    def __exit__(self, exc_type, exc, tb):
        if self.path is not None:
            self.path.unlink()
        return False


if __name__ == "__main__":
    unittest.main()
