# TermShow

🎞️ A simple terminal-based slideshow tool written in Python.

## Features

- Slide types: text, art (e.g. toilet/figlet), and options
- Display with or without page numbers
- Works in most Unix-like terminals
- Simple slide format

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/termshow.git
cd termshow
```

(Optionally) create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install required tools (if not installed):

```bash
sudo apt install toilet figlet
```

## Usage

Run a slide file:

```bash
python3 termshow.py slides/demo.slide
```

### Options:

- `--no-page-number`: Hide page number indicator (e.g. `█ 1/3`)

## Slide Format

Example slide file:

```txt
::: text
Welcome to TermShow!
This is a simple terminal-based slideshow tool.

::: art
toilet "HELLO" --gay

::: options
1. Start
2. Help
3. Exit
```

## License

MIT License
