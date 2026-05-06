import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class WordPosition:
    word: str
    row: int
    col: int
    vertical: bool
    number: int = 0

class Crossword:
    def __init__(self, words: List[str], max_attempts: int = 50):
        self.words = [word.upper() for word in words]
        self.max_attempts = max_attempts
        self.grid_size = max(20, max(len(word) for word in self.words) * 2)
        self.grid = [[' ' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.positions: List[WordPosition] = []
        
    def can_place_word(self, word: str, row: int, col: int, vertical: bool) -> bool:
        """Check if a word can be placed at the given position."""
        if vertical:
            if row + len(word) > self.grid_size:
                return False
            for i, char in enumerate(word):
                if self.grid[row + i][col] not in (' ', char):
                    return False
        else:
            if col + len(word) > self.grid_size:
                return False
            for i, char in enumerate(word):
                if self.grid[row][col + i] not in (' ', char):
                    return False
        return True
    
    def place_word(self, word: str, row: int, col: int, vertical: bool) -> None:
        """Place a word on the grid."""
        if vertical:
            for i, char in enumerate(word):
                self.grid[row + i][col] = char
        else:
            for i, char in enumerate(word):
                self.grid[row][col + i] = char
    
    def generate(self) -> bool:
        """Generate the crossword puzzle."""
        if not self.words:
            return False
            
        # Start with the longest word in the center
        first_word = max(self.words, key=len)
        row = (self.grid_size - len(first_word)) // 2
        col = (self.grid_size - max(len(w) for w in self.words)) // 2
        
        self.place_word(first_word, row, col, False)
        self.positions.append(WordPosition(first_word, row, col, False, 1))
        remaining_words = [w for w in self.words if w != first_word]
        
        # Try to place other words
        word_number = 2
        for word in sorted(remaining_words, key=len, reverse=True):
            placed = False
            for attempt in range(self.max_attempts):
                # Try to place word intersecting with existing words
                for pos in random.sample(self.positions, len(self.positions)):
                    if random.choice([True, False]):  # Try both directions
                        # Try placing vertically if current is horizontal and vice versa
                        if not pos.vertical:
                            # Try to place vertically
                            for i, char in enumerate(pos.word):
                                if char in word:
                                    word_idx = word.index(char)
                                    new_row = pos.row - word_idx
                                    new_col = pos.col + i
                                    if self.can_place_word(word, new_row, new_col, True):
                                        self.place_word(word, new_row, new_col, True)
                                        self.positions.append(WordPosition(word, new_row, new_col, True, word_number))
                                        word_number += 1
                                        placed = True
                                        break
                            if placed:
                                break
                            
                            # Try to place horizontally if current is vertical
                        else:
                            for i, char in enumerate(pos.word):
                                if char in word:
                                    word_idx = word.index(char)
                                    new_row = pos.row + i
                                    new_col = pos.col - word_idx
                                    if self.can_place_word(word, new_row, new_col, False):
                                        self.place_word(word, new_row, new_col, False)
                                        self.positions.append(WordPosition(word, new_row, new_col, False, word_number))
                                        word_number += 1
                                        placed = True
                                        break
                            if placed:
                                break
                    
                    if placed:
                        break
                
                if placed:
                    break
        
        return True
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Get the bounding box of the crossword."""
        min_row = min_col = self.grid_size
        max_row = max_col = 0
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.grid[i][j] != ' ':
                    min_row = min(min_row, i)
                    min_col = min(min_col, j)
                    max_row = max(max_row, i)
                    max_col = max(max_col, j)
        
        return min_row, min_col, max_row, max_col
    
    def to_markdown(self) -> str:
        """Convert the crossword to markdown format."""
        min_row, min_col, max_row, max_col = self.get_bounds()
        
        # Add padding
        min_row = max(0, min_row - 1)
        min_col = max(0, min_col - 1)
        max_row = min(self.grid_size - 1, max_row + 1)
        max_col = min(self.grid_size - 1, max_col + 1)
        
        # Create markdown content
        lines = ["# CROSSWORD SOLUTION\n"]
        
        # Add word bank
        lines.append("## WORD BANK\n")
        for pos in sorted(self.positions, key=lambda x: x.number):
            direction = "Down" if pos.vertical else "Across"
            lines.append(f"- {pos.number}. {pos.word} ({direction})")
        
        # Add crossword grid
        lines.append("\n## CROSSWORD SOLUTION\n")
        lines.append("```")
        
        # Add column numbers
        header = "  " + " ".join(str(i % 10) for i in range(min_col, max_col + 1))
        lines.append(header)
        
        # Add rows with row numbers and content
        for i in range(min_row, max_row + 1):
            row = [str(i % 10)]
            for j in range(min_col, max_col + 1):
                row.append(self.grid[i][j] if self.grid[i][j] != ' ' else '·')
            lines.append(" ".join(row))
        
        lines.append("```")
        
        return "\n".join(lines)

def generate_crossword(words: List[str]) -> str:
    """Generate a crossword puzzle from a list of words."""
    max_attempts = 10
    for _ in range(max_attempts):
        crossword = Crossword(words)
        if crossword.generate():
            return crossword.to_markdown()
    return "Failed to generate crossword after multiple attempts."

def process_input_files():
    """Process all .txt files in the Input directory."""
    input_dir = Path("Input")
    output_dir = Path("Output")
    output_dir.mkdir(exist_ok=True)
    
    for input_file in input_dir.glob("*.txt"):
        with open(input_file, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        
        if not words:
            print(f"No words found in {input_file.name}")
            continue
        
        # Generate crossword
        markdown = generate_crossword(words)
        
        # Write to output file
        output_file = output_dir / f"{input_file.stem}_crossword.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"Created: {output_file}")

if __name__ == "__main__":
    process_input_files()
