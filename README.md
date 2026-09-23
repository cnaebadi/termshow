# TermShow

🎞️ **TermShow** is a simple terminal-based slideshow tool written in Python, designed for Unix-like environments.

## ✨ Features

- Support for multiple slide types:
  - `text`: normal text
  - `art`: shell commands like `toilet`, `figlet`, etc.
  - `options`: list-style options
- Centered slides (default), or `left` to pin content to the left
- Text styles: normal, bold, and four header sizes (`h1`–`h4`)
- Typewriter effect (optional)
- Navigate using arrow keys
- Auto-play mode with custom delay
- Slide numbering (can be disabled)
- Simple and readable slide format

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/termshow.git
cd termshow
```

### 2. Install with pip

```bash
pip install .
```

> For development (editable mode):
>
> ```bash
> pip install -e .
> ```

### 3. Install optional tools (for `art` slides)

```bash
sudo apt install toilet
```

## 🖥️ Usage

After installation, you can run the tool using:

```bash
termshow slides/demo.slide
```

### Options:

- `--no-page-number` – Hide the slide number (e.g., `██ 2/5`)
- `-t` – Type normal text, bold text, and headers one character at a time

### Navigation:

- `↑` / `↓` – Move between slides
- `'a'` key – Start auto-play mode (with user-defined delay)
- `'q'` key – Quit slideshow

## 📝 Slide Format

Each slide starts with a `:::` followed by the type. Add `left` to keep that slide on the left side. Slides are centered by default.

```
::: text
::: text left
::: options center
::: art left
```

On `text` and `options` slides, a line can set its size:

| Write this | Result |
| --- | --- |
| `h1: Title` or `# Title` | Largest header |
| `h2: Title` or `## Title` | Second header size |
| `h3: Title` or `### Title` | Third header size |
| `h4: Title` or `#### Title` | Smallest header |
| `bold: Text` or `**Text**` | Bold |
| anything else | Normal |

Latin headers are drawn as block letters, and the size shrinks automatically when the terminal is too small. Other scripts (for example Persian) stay as colored bold text, because the terminal font cannot be scaled.

Example `slides/demo.slide`:

```
::: text
h1: TermShow
h2: Hi
A normal line with a **bold** word.

::: text left
h3: Left
h4: Side
bold: This whole line is bold

::: art
toilet "HELLO"
# Avoid using color effects like '--gay' as they may not render properly in the terminal UI.

::: options
1. Start
2. Help
3. Exit
```

## 🛠️ Development

If you're working on the code:

```bash
# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate

# Install the project in editable mode
pip install -e .
```

Run the tests:

```bash
python3 -m unittest discover -s tests -v
```

To check that coverage stays complete, install `coverage` and run:

```bash
python3 -m pip install coverage
python3 -m coverage run --branch -m unittest discover -s tests
python3 -m coverage report -m
```

The tests cover slide parsing, centering, header sizes, bold text, the typewriter effect (`-t`, including headers), art commands, auto-play, and keyboard navigation.

## 📄 License

MIT License © Sina Ebadi
