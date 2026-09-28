# Worksheet Tools

A collection of Python scripts for generating various educational worksheets (word searches, crosswords, scrambles, etc.).

## Crossword generator

`crossword_generator.py` reads every `.txt` and `.md` file in `Input/` and writes two HTML files per input to `Output/`:

- `<name>_crossword.html` — the puzzle. Students can type in the grid (arrow keys move, clicking a clue jumps to it, clicking a crossing cell twice switches Across/Down) or print it. The page contains no answers.
- `<name>_crossword_key.html` — the answer key.

### Input format

```
seed: 482913
title: Vegetables

carrot | An orange root vegetable that rabbits love
sweet potato | An orange potato that tastes sweet
corn - Yellow kernels that can become popcorn
onion: This vegetable can make you cry when you cut it
```

- **seed** (top of the file) decides the layout. The same seed and the same vocab list always make the same puzzle. If a file has no seed, the script picks one and writes it to the top of the file for you. Change the seed to get a different layout. Any text works as a seed.
- **title** is optional. If you leave it out, the file name is used.
- Each vocab line is `word | clue`. `word - clue` and `word: clue` work too. Multi-word answers like "sweet potato" are fine; the clue shows the letter counts, e.g. (5, 6).
- In `.md` files, list bullets (`- `), bold (`**word**`), `#` headings and tables (`| Word | Question |`) are all understood.
- Plain word lists (no clues) are skipped, so the same `Input/` folder can still hold word lists for the other tools.

The seed is also printed in small, light-gray text at the bottom-right of both pages (and in a `crossword-seed` meta tag), so you can find the seed for any printed puzzle and regenerate its answer key.
