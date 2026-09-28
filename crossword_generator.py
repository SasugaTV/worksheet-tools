"""Crossword generator.

Reads vocab + clue files from Input/Crossword/ (.txt or .md) and writes an interactive
HTML puzzle plus a separate answer key to Output/. The layout is driven by the
seed at the top of each input file, so the same seed + same vocab list always
produces the same puzzle. See README.md for the input format.
"""
import html
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

LAYOUT_ATTEMPTS = 80  # candidate layouts tried per puzzle; the best one wins

ACROSS, DOWN = 1, 2

HEADER_KEYS = ("seed", "title")
TABLE_HEADER_WORDS = {"word", "words", "vocab", "vocabulary", "answer", "answers", "term"}


@dataclass
class Entry:
    answer: str  # as written in the input file, e.g. "ice cream"
    clue: str

    @property
    def letters(self) -> str:
        return "".join(ch for ch in self.answer.upper() if ch.isalpha())

    @property
    def enumeration(self) -> str:
        """Letter counts for multi-word answers, e.g. "(3, 5)"; empty for single words."""
        parts = [p for p in re.split(r"[^\w]+", self.answer) if p]
        return f"({', '.join(str(len(p)) for p in parts)})" if len(parts) > 1 else ""


@dataclass
class Placement:
    entry: Entry
    row: int
    col: int
    down: bool
    number: int = 0

    def cells(self) -> List[Tuple[int, int]]:
        dr, dc = (1, 0) if self.down else (0, 1)
        return [(self.row + dr * i, self.col + dc * i) for i in range(len(self.entry.letters))]


@dataclass
class PuzzleInput:
    title: str
    seed: Optional[str]
    entries: List[Entry] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def _strip_markdown(line: str) -> str:
    line = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", line)  # list markers
    return line.replace("**", "").replace("__", "").strip()


def _split_entry(line: str) -> Optional[Tuple[str, str]]:
    """Split "word | clue", "word - clue" or "word: clue" into (word, clue)."""
    if "|" in line:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        cells = [c for c in cells if c]
        if len(cells) >= 2:
            return cells[0], " | ".join(cells[1:])
        return None
    for sep in (" - ", " – ", " — ", ":"):
        if sep in line:
            word, clue = line.split(sep, 1)
            if word.strip() and clue.strip():
                return word.strip(), clue.strip()
    return None


def parse_input(path: Path) -> PuzzleInput:
    text = path.read_text(encoding="utf-8-sig")
    puzzle = PuzzleInput(title=path.stem.replace("_", " ").replace("-", " ").title(), seed=None)
    in_comment = False

    for raw in text.splitlines():
        line = raw.strip()
        if in_comment:
            in_comment = "-->" not in line
            continue
        if line.startswith("<!--"):
            in_comment = "-->" not in line
            continue
        if not line or line.startswith("#") and not re.match(r"#+\s*(seed|title)\s*:", line, re.I):
            continue
        if re.fullmatch(r"[\s|:\-]+", line):  # markdown table separator row
            continue

        line = _strip_markdown(line.lstrip("#").strip() if line.startswith("#") else line)

        # Header lines (seed/title) are only recognised before the first vocab entry
        if not puzzle.entries:
            m = re.match(r"(seed|title)\s*:\s*(.*)$", line, re.I)
            if m:
                key, value = m.group(1).lower(), m.group(2).strip()
                if key == "seed" and value:
                    puzzle.seed = value
                elif key == "title" and value:
                    puzzle.title = value
                continue

        pair = _split_entry(line)
        if pair is None:
            continue
        word, clue = pair
        if word.lower() in TABLE_HEADER_WORDS and not puzzle.entries:
            continue
        puzzle.entries.append(Entry(word, clue))

    return puzzle


def ensure_seed(path: Path, puzzle: PuzzleInput) -> str:
    """Return the file's seed, writing a new one to the top of the file if it has none."""
    if puzzle.seed:
        return puzzle.seed
    seed = str(random.SystemRandom().randint(100000, 999999))
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        original = f.read()
    newline = "\r\n" if "\r\n" in original else "\n"
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(f"seed: {seed}{newline}{original}")
    print(f"  No seed in {path.name}; added 'seed: {seed}' to the top of the file.")
    puzzle.seed = seed
    return seed


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

class Layout:
    def __init__(self):
        self.letters: Dict[Tuple[int, int], str] = {}
        self.dirs: Dict[Tuple[int, int], int] = {}
        self.placements: List[Placement] = []
        self.crossings = 0

    def bounds(self) -> Tuple[int, int, int, int]:
        rows = [r for r, _ in self.letters]
        cols = [c for _, c in self.letters]
        return min(rows), min(cols), max(rows), max(cols)

    def check(self, word: str, row: int, col: int, down: bool) -> Optional[int]:
        """Number of crossings if the word fits here, else None."""
        dr, dc = (1, 0) if down else (0, 1)
        direction = DOWN if down else ACROSS
        if (row - dr, col - dc) in self.letters:
            return None
        if (row + dr * len(word), col + dc * len(word)) in self.letters:
            return None
        crossings = 0
        for i, ch in enumerate(word):
            cell = (row + dr * i, col + dc * i)
            existing = self.letters.get(cell)
            if existing is None:
                # An empty cell must not touch letters on either side, or it would form a junk word
                if (cell[0] + dc, cell[1] + dr) in self.letters or (cell[0] - dc, cell[1] - dr) in self.letters:
                    return None
            elif existing != ch or self.dirs[cell] & direction:
                return None
            else:
                crossings += 1
        return crossings

    def place(self, entry: Entry, row: int, col: int, down: bool, crossings: int) -> None:
        placement = Placement(entry, row, col, down)
        direction = DOWN if down else ACROSS
        for cell, ch in zip(placement.cells(), entry.letters):
            self.letters[cell] = ch
            self.dirs[cell] = self.dirs.get(cell, 0) | direction
        self.placements.append(placement)
        self.crossings += crossings

    def candidates(self, word: str) -> List[Tuple[int, int, bool, int]]:
        found = []
        for (r, c), ch in self.letters.items():
            if self.dirs[(r, c)] == ACROSS | DOWN:
                continue
            down = self.dirs[(r, c)] == ACROSS  # cross perpendicular to the existing word
            for i, wch in enumerate(word):
                if wch != ch:
                    continue
                row, col = (r - i, c) if down else (r, c - i)
                crossings = self.check(word, row, col, down)
                if crossings:
                    found.append((row, col, down, crossings))
        return found


def _build_layout(entries: List[Entry], rng: random.Random) -> Layout:
    order = sorted(entries, key=lambda e: len(e.letters) + rng.random() * 3, reverse=True)
    layout = Layout()
    first = order[0]
    layout.place(first, 0, 0, rng.random() < 0.5, 0)

    pending = order[1:]
    progress = True
    while pending and progress:
        progress = False
        still_pending = []
        for entry in pending:
            options = layout.candidates(entry.letters)
            if not options:
                still_pending.append(entry)
                continue
            min_r, min_c, max_r, max_c = layout.bounds()

            def score(option):
                row, col, down, crossings = option
                end_r = row + (len(entry.letters) - 1 if down else 0)
                end_c = col + (0 if down else len(entry.letters) - 1)
                h = max(max_r, end_r) - min(min_r, row) + 1
                w = max(max_c, end_c) - min(min_c, col) + 1
                return crossings * 3 - h * w * 0.02 - abs(h - w) * 0.4 + rng.random() * 1.5

            row, col, down, crossings = max(options, key=score)
            layout.place(entry, row, col, down, crossings)
            progress = True
        pending = still_pending
    return layout


def generate_layout(entries: List[Entry], seed: str) -> Layout:
    rng = random.Random(seed)
    best, best_key = None, None
    for _ in range(LAYOUT_ATTEMPTS):
        layout = _build_layout(entries, rng)
        min_r, min_c, max_r, max_c = layout.bounds()
        h, w = max_r - min_r + 1, max_c - min_c + 1
        key = (len(layout.placements), layout.crossings - max(h, w), -h * w)
        if best_key is None or key > best_key:
            best, best_key = layout, key

    # Shift to (0, 0) and number the words in reading order
    min_r, min_c, _, _ = best.bounds()
    for p in best.placements:
        p.row -= min_r
        p.col -= min_c
    best.letters = {(r - min_r, c - min_c): ch for (r, c), ch in best.letters.items()}
    starts = sorted({(p.row, p.col) for p in best.placements})
    numbers = {cell: i for i, cell in enumerate(starts, 1)}
    for p in best.placements:
        p.number = numbers[(p.row, p.col)]
    return best


# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------

CSS = """
:root { --ink: #1d2433; --muted: #5b6475; --line: #1d2433; --hl: #fff3b0; --hl-word: #e3efff; --accent: #2f6fdf; }
* { box-sizing: border-box; }
body { margin: 0; background: #f6f7f9; color: var(--ink); font: 16px/1.45 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.page { max-width: 1100px; margin: 0 auto; padding: 24px 16px 12px; background: #fff; min-height: 100vh; }
h1 { margin: 0 0 4px; font-size: 1.8rem; letter-spacing: .01em; }
.meta { display: flex; flex-wrap: wrap; gap: 8px 32px; color: var(--muted); margin: 6px 0 20px; }
.meta span { min-width: 220px; border-bottom: 1px solid #b9bfca; padding-bottom: 2px; }
.key-badge { display: inline-block; font-size: .8rem; font-weight: 600; color: #b3261e; border: 1px solid #b3261e; border-radius: 4px; padding: 1px 6px; vertical-align: middle; margin-left: 8px; }
.layout { display: flex; flex-wrap: wrap; gap: 28px; align-items: flex-start; }
.grid-wrap { flex: 0 1 auto; max-width: 100%; overflow-x: auto; }
.grid { display: grid; grid-template-columns: repeat(var(--cols), var(--cell)); grid-auto-rows: var(--cell);
        --cell: clamp(22px, calc((100vw - 48px) / var(--cols)), 38px); }
.cell { position: relative; }
.cell.on { background: #fff; outline: 1.5px solid var(--line); outline-offset: -0.75px; }
.cell .num { position: absolute; top: 1px; left: 2px; font-size: calc(var(--cell) * .28); line-height: 1; color: var(--ink); pointer-events: none; }
.cell input, .cell .ans { width: 100%; height: 100%; border: 0; padding: calc(var(--cell) * .18) 0 0; margin: 0; background: transparent;
        text-align: center; font: 600 calc(var(--cell) * .52) system-ui, sans-serif; color: var(--ink); text-transform: uppercase; caret-color: transparent; }
.cell .ans { display: flex; align-items: center; justify-content: center; color: #b3261e; }
.cell input:focus { outline: none; }
.cell.word { background: var(--hl-word); }
.cell.cur { background: var(--hl); }
.clues { flex: 1 1 320px; display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 8px 28px; }
.clues h2 { font-size: 1.05rem; text-transform: uppercase; letter-spacing: .08em; margin: 0 0 6px; border-bottom: 2px solid var(--ink); padding-bottom: 3px; }
.clues ol { list-style: none; margin: 0; padding: 0; }
.clues li { display: flex; gap: 8px; padding: 3px 6px; border-radius: 4px; cursor: pointer; }
.clues li b { min-width: 1.6em; text-align: right; }
.clues li.active { background: var(--hl-word); }
.clues .answer { color: #b3261e; font-weight: 600; margin-left: 4px; }
.enum { color: var(--muted); white-space: nowrap; }
.tools { margin: 20px 0 0; display: flex; gap: 8px; }
.tools button { font: inherit; font-size: .9rem; padding: 6px 14px; border: 1px solid #c4cad4; background: #fff; border-radius: 6px; cursor: pointer; color: var(--ink); }
.tools button:hover { border-color: var(--accent); color: var(--accent); }
.ref { margin-top: 28px; text-align: right; font-size: 9px; color: #d4d7dc; user-select: all; }
@media print {
  body { background: #fff; }
  .page { padding: 0; min-height: 0; }
  .tools { display: none; }
  .grid { --cell: 30px; }
  .cell.word, .cell.cur { background: #fff; }
  .clues li { break-inside: avoid; }
}
"""

JS = """
const words = JSON.parse(document.getElementById('words').textContent);
const grid = document.querySelector('.grid');
const inputs = {};
grid.querySelectorAll('input').forEach(el => { inputs[el.dataset.r + ',' + el.dataset.c] = el; });
const cellWords = {};
words.forEach(w => w.cells.forEach(([r, c]) => (cellWords[r + ',' + c] ||= {})[w.dir] = w));
let dir = 'across', current = null;

function wordAt(key) { const m = cellWords[key] || {}; return m[dir] || m.across || m.down; }
function highlight() {
  document.querySelectorAll('.cell.word, .cell.cur').forEach(el => el.classList.remove('word', 'cur'));
  document.querySelectorAll('.clues li.active').forEach(el => el.classList.remove('active'));
  if (!current) return;
  const w = wordAt(current);
  if (!w) return;
  dir = w.dir;
  w.cells.forEach(([r, c]) => inputs[r + ',' + c].parentElement.classList.add('word'));
  inputs[current].parentElement.classList.add('cur');
  const li = document.getElementById('clue-' + w.id);
  if (li) li.classList.add('active');
}
function focusCell(key) { if (inputs[key]) { inputs[key].focus(); } }
function step(key, delta) {
  const w = wordAt(key); if (!w) return;
  const i = w.cells.findIndex(([r, c]) => r + ',' + c === key) + delta;
  if (i >= 0 && i < w.cells.length) focusCell(w.cells[i].join(','));
}
function move(key, dr, dc) {
  let [r, c] = key.split(',').map(Number);
  for (let n = 0; n < 60; n++) { r += dr; c += dc; if (inputs[r + ',' + c]) return focusCell(r + ',' + c); }
}
Object.entries(inputs).forEach(([key, el]) => {
  el.addEventListener('focus', () => { current = key; highlight(); });
  el.addEventListener('mousedown', () => {
    if (current === key && (cellWords[key] || {}).across && (cellWords[key] || {}).down) {
      dir = dir === 'across' ? 'down' : 'across'; setTimeout(highlight);
    }
  });
  el.addEventListener('keydown', e => {
    const arrows = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
    if (arrows[e.key]) {
      e.preventDefault();
      const d = arrows[e.key][0] ? 'down' : 'across';
      if ((cellWords[key] || {})[d]) dir = d;
      move(key, ...arrows[e.key]);
    } else if (e.key === 'Backspace') {
      e.preventDefault();
      if (el.value) el.value = ''; else { step(key, -1); if (inputs[current]) inputs[current].value = ''; }
    } else if (e.key === 'Delete') {
      e.preventDefault(); el.value = '';
    } else if (e.key.length === 1 && /\\p{L}/u.test(e.key) && !e.ctrlKey && !e.metaKey) {
      e.preventDefault(); el.value = e.key.toUpperCase(); step(key, 1);
    }
  });
});
document.querySelectorAll('.clues li').forEach(li => li.addEventListener('click', () => {
  const w = words.find(w => 'clue-' + w.id === li.id);
  dir = w.dir; focusCell(w.cells[0].join(','));
}));
document.getElementById('clear').addEventListener('click', () => {
  if (confirm('Clear all your answers?')) Object.values(inputs).forEach(el => el.value = '');
});
document.getElementById('print').addEventListener('click', () => window.print());
"""


def render_html(puzzle: PuzzleInput, layout: Layout, answer_key: bool) -> str:
    esc = html.escape
    _, _, max_r, max_c = layout.bounds()
    rows, cols = max_r + 1, max_c + 1
    numbers = {(p.row, p.col): p.number for p in layout.placements}

    cells = []
    for r in range(rows):
        for c in range(cols):
            ch = layout.letters.get((r, c))
            if ch is None:
                cells.append('<div class="cell"></div>')
                continue
            num = f'<span class="num">{numbers[(r, c)]}</span>' if (r, c) in numbers else ""
            if answer_key:
                body = f'<span class="ans">{esc(ch)}</span>'
            else:
                body = (f'<input data-r="{r}" data-c="{c}" maxlength="1" autocomplete="off" '
                        f'autocapitalize="characters" spellcheck="false" aria-label="row {r + 1} column {c + 1}">')
            cells.append(f'<div class="cell on">{num}{body}</div>')

    def clue_list(down: bool) -> str:
        items = []
        for p in sorted((p for p in layout.placements if p.down == down), key=lambda p: p.number):
            enum = f' <span class="enum">{esc(p.entry.enumeration)}</span>' if p.entry.enumeration else ""
            answer = f' <span class="answer">{esc(p.entry.answer.upper())}</span>' if answer_key else ""
            items.append(f'<li id="clue-{p.number}{"d" if down else "a"}"><b>{p.number}</b>'
                         f'<span>{esc(p.entry.clue)}{enum}{answer}</span></li>')
        return "\n".join(items)

    title = esc(puzzle.title)
    heading = f'{title}<span class="key-badge">ANSWER KEY</span>' if answer_key else title
    meta = "" if answer_key else '<div class="meta"><span>Name:</span><span>Date:</span></div>'

    script = ""
    if not answer_key:
        words = [{"id": f'{p.number}{"d" if p.down else "a"}', "dir": "down" if p.down else "across",
                  "cells": [list(cell) for cell in p.cells()]} for p in layout.placements]
        script = (f'<script type="application/json" id="words">{json.dumps(words)}</script>\n'
                  f'<script>{JS}</script>')
    tools = "" if answer_key else ('<div class="tools"><button id="print" type="button">Print</button>'
                                   '<button id="clear" type="button">Clear</button></div>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="crossword-seed" content="{esc(puzzle.seed)}">
<title>{title}{" (Answer Key)" if answer_key else ""}</title>
<style>{CSS}</style>
</head>
<body>
<div class="page">
<h1>{heading}</h1>
{meta}
<div class="layout">
<div class="grid-wrap"><div class="grid" style="--cols: {cols}">
{"".join(cells)}
</div></div>
<div class="clues">
<section><h2>Across</h2><ol>
{clue_list(False)}
</ol></section>
<section><h2>Down</h2><ol>
{clue_list(True)}
</ol></section>
</div>
</div>
{tools}
<div class="ref" title="Puzzle seed">seed {esc(puzzle.seed)}</div>
</div>
{script}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def process_file(input_path: Path, output_dir: Path) -> None:
    puzzle = parse_input(input_path)
    if not puzzle.entries:
        print(f"Skipping {input_path.name}: no 'word | clue' lines found.")
        return

    seen, entries = set(), []
    for entry in puzzle.entries:
        if len(entry.letters) < 2:
            print(f"  Skipping '{entry.answer}' in {input_path.name}: answers need at least 2 letters.")
        elif entry.letters in seen:
            print(f"  Skipping duplicate '{entry.answer}' in {input_path.name}.")
        else:
            seen.add(entry.letters)
            entries.append(entry)
    if not entries:
        print(f"Skipping {input_path.name}: no usable entries.")
        return
    puzzle.entries = entries

    seed = ensure_seed(input_path, puzzle)
    layout = generate_layout(puzzle.entries, seed)

    placed = {id(p.entry) for p in layout.placements}
    missed = [e.answer for e in puzzle.entries if id(e) not in placed]
    if missed:
        print(f"  Warning: couldn't connect {', '.join(missed)} in {input_path.name}. "
              f"Try a different seed or add words that share letters with them.")

    for suffix, answer_key in (("crossword", False), ("crossword_key", True)):
        output_file = output_dir / f"{input_path.stem}_{suffix}.html"
        output_file.write_text(render_html(puzzle, layout, answer_key), encoding="utf-8")
        print(f"Created: {output_file}")


def main():
    base_dir = Path(__file__).parent
    # Crossword files live in their own subfolder because they use a different
    # format (seed + clues) from the plain word lists the other tools read.
    input_dir = base_dir / "Input" / "Crossword"
    output_dir = base_dir / "Output"

    output_dir.mkdir(exist_ok=True)

    if not input_dir.is_dir():
        input_dir.mkdir(parents=True)
        print(f"Created {input_dir}. Put crossword files there (see examples/crossword_example.md).")
        return

    input_files = sorted(list(input_dir.glob("*.txt")) + list(input_dir.glob("*.md")))
    if not input_files:
        print(f"No .txt or .md files found in {input_dir}")
        return

    for input_file in input_files:
        process_file(input_file, output_dir)


if __name__ == "__main__":
    main()
