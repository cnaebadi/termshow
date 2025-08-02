# TermShow

🎞️ **TermShow** is a simple terminal-based slideshow tool written in Python, designed for Unix-like environments.

## ✨ Features

- Support for multiple slide types:
  - `text`: normal text
  - `art`: shell commands like `toilet`, `figlet`, etc.
  - `options`: list-style options
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
- `-t` – Enable typewriter animation effect

### Navigation:

- `↑` / `↓` – Move between slides
- `'a'` key – Start auto-play mode (with user-defined delay)
- `'q'` key – Quit slideshow

## 📝 Slide Format

Each slide starts with a `:::` followed by the type.

Example `slides/demo.slide`:

```
::: text
Welcome to TermShow!
This is a simple terminal-based slideshow tool.

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

# Install dependencies and project in editable mode
pip install -e .
```

## 📄 License

MIT License © Sina Ebadi
