import os
import argparse
import curses
import time
import subprocess
import time

def typewriter_print(stdscr, text, delay=0.05):
    for ch in text:
        stdscr.addstr(ch)
        stdscr.refresh()
        time.sleep(delay)


def parse_slide_file(path):
    with open(path, 'r') as f:
        lines = f.read().split('\n')

    slides = []
    current = {'type': 'text', 'content': []}

    for line in lines:
        if line.strip().startswith(":::"):
            if current['content']:
                slides.append(current)
            current = {'type': line.strip()[3:].strip(), 'content': []}
        else:
            current['content'].append(line)
    if current['content']:
        slides.append(current)

    return slides


def render_slide(stdscr, slide, index, total, show_page,typewriter):
    stdscr.clear()

    if show_page:
        stdscr.addstr(f"██ {index+1}/{total}\n\n")

    if slide['type'] == 'art':
        for line in slide['content']:
            try:
                output = subprocess.check_output(line, shell=True, text=True)
                stdscr.addstr(output)
            except subprocess.CalledProcessError as e:
                stdscr.addstr(f"[!] Command failed: {line}\n{e}\n")
    elif slide['type'] == 'options':
        if typewriter:
            for line in slide['content']:
                typewriter_print(stdscr, f"  {line}\n")
        else:
           for line in slide['content']:
            stdscr.addstr(f"  {line}\n")
    else:
        if typewriter:
            for line in slide['content']:
                typewriter_print(stdscr, line + '\n')
        else:
            for line in slide['content']:
                stdscr.addstr(line + '\n')

    stdscr.refresh()



def prompt_delay(stdscr):
    curses.echo()
    stdscr.addstr("\nEnter auto-play delay in seconds (0-1000): ")
    stdscr.refresh()
    input_str = stdscr.getstr().decode('utf-8')
    curses.noecho()
    try:
        value = int(input_str)
        if 0 <= value <= 1000:
            return value
    except ValueError:
        pass
    return None

def slideshow(stdscr, slides, show_page,typewriter):
    index = 0
    total = len(slides)
    auto_mode = False
    delay = 3

    if typewriter:
        stdscr.addstr('umade inja' + '\n')
    else:
        stdscr.addstr('nayumade inja' + '\n')

    stdscr.nodelay(False)
    render_slide(stdscr, slides[index], index, total, show_page,typewriter)
    stdscr.addstr("\nUse ↑/↓ to navigate, 'a' for auto, 'q' to quit.")
    stdscr.refresh()

    while True:
        key = stdscr.getch()

        if key == curses.KEY_UP:
            if index > 0:
                index -= 1
                render_slide(stdscr, slides[index], index, total, show_page,typewriter)

        elif key == curses.KEY_DOWN:
            if index < total - 1:
                index += 1
                render_slide(stdscr, slides[index], index, total, show_page,typewriter)

        elif key == ord('q'):
            break

        elif key == ord('a'):
            d = prompt_delay(stdscr)
            if d is not None:
                delay = d
                auto_mode = True
                stdscr.nodelay(True)
                start = time.time()
            else:
                render_slide(stdscr, slides[index], index, total, show_page,typewriter)
                stdscr.addstr("\nInvalid input. Press any key to continue.")
                stdscr.getch()
                render_slide(stdscr, slides[index], index, total, show_page,typewriter)

        if auto_mode:
            time.sleep(delay)
            if index < total - 1:
                index += 1
                render_slide(stdscr, slides[index], index, total, show_page,typewriter)
            else:
                auto_mode = False
                stdscr.nodelay(False)


def main():
    parser = argparse.ArgumentParser(description="Terminal slideshow with curses")
    parser.add_argument("file", help="Path to slide file")
    parser.add_argument("--no-page-number", action="store_true", help="Hide slide number display")
    parser.add_argument(
    "-t",
    action="store_true",
    help="Show slide text with typewriter effect"
    )
    args = parser.parse_args()

    slides = parse_slide_file(args.file)
    curses.wrapper(slideshow, slides, not args.no_page_number, args.t)



if __name__ == "__main__":
    main()
