import os
import random
import string
from pathlib import Path
from typing import List, Tuple, Set, Optional

class WordSearch:
    def __init__(self, words: List[str], size: Optional[int] = None):
        self.words = [word.upper().replace(' ', '') for word in words]
        self.longest_word = max(len(word) for word in self.words) if self.words else 0
        self.size = size or max(self.longest_word + 2, 10)  # Minimum size 10x10
        self.grid = [[None for _ in range(self.size)] for _ in range(self.size)]
        self.placed_words = set()
        self.word_positions = []  # Store (word, row, col, dx, dy) for each placed word
        
        # Define directions for different difficulty levels
        self.directions = {
            'easy': [(0, 1), (1, 0)],  # Right, Down
            'medium': [(0, 1), (1, 0), (1, 1), (1, -1)],  # + Diagonals
            'hard': [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]  # All 8 directions
        }

    def can_place_word(self, word: str, row: int, col: int, dx: int, dy: int) -> bool:
        """Check if word can be placed at position (row,col) in direction (dx,dy)."""
        # Check boundaries
        if (row < 0 or col < 0 or 
            row + (len(word)-1)*dy >= self.size or 
            row + (len(word)-1)*dy < 0 or
            col + (len(word)-1)*dx >= self.size or
            col + (len(word)-1)*dx < 0):
            return False
            
        # Check each character position for conflicts
        for i in range(len(word)):
            r = row + i*dy
            c = col + i*dx
            if self.grid[r][c] is not None and self.grid[r][c] != word[i]:
                return False
        
        return True

    def place_word(self, word: str, difficulty: str) -> bool:
        """Try to place a word on the grid with intersections allowed."""
        word = word.upper().replace(' ', '')
        if word in self.placed_words:
            return True
            
        directions = self.directions[difficulty]
        # Don't shuffle directions for consistent results
        
        # Try to place the word, allowing intersections
        for row in range(self.size):
            for col in range(self.size):
                for dx, dy in directions:
                    if self.can_place_word(word, row, col, dx, dy):
                        self._place_word(word, row, col, dx, dy)
                        return True
        return False

    def _place_word(self, word: str, row: int, col: int, dx: int, dy: int) -> None:
        """Place a word on the grid."""
        for i, char in enumerate(word):
            r = row + i*dy
            c = col + i*dx
            self.grid[r][c] = char
        self.placed_words.add(word)
        self.word_positions.append((word, row, col, dx, dy))

    def fill_grid(self) -> None:
        """Fill empty cells with spaces to avoid coincidental patterns."""
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] is None:
                    self.grid[i][j] = ' '

    def create_solution_grid(self) -> List[List[str]]:
        """Create a grid showing only the placed words."""
        # Create a grid of spaces
        solution = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        
        # Place the actual words in the solution using tracked positions
        for word, row, col, dx, dy in self.word_positions:
            for i, char in enumerate(word):
                r = row + i * dy
                c = col + i * dx
                solution[r][c] = char
        return solution

def create_intersecting_word_search(words: List[str], difficulty: str, max_attempts: int = 50) -> WordSearch:
    """Create a word search puzzle with intersecting words."""
    if not words:
        raise ValueError("No words provided for word search")
    
    # Ensure we have valid words and process to remove spaces
    words = [word.upper().replace(' ', '') for word in words if word.strip()]
    if not words:
        raise ValueError("No valid words provided")
    
    # Calculate initial grid size based on longest processed word and number of words
    max_word_len = max(len(word) for word in words)
    initial_size = max(max_word_len + 2, 10, int((len(words) * max_word_len) ** 0.5) + 2)
    
    # Try with increasing grid sizes
    for size in range(initial_size, initial_size + 15):  # Increased range for longer words
        for attempt in range(max_attempts):
            ws = WordSearch(words, size)
            ws.grid = [[None for _ in range(size)] for _ in range(size)]
            
            all_placed = True
            # Sort by length (longest first) for better placement
            sorted_words = sorted(words, key=lambda x: (-len(x), x))
            
            for word in sorted_words:
                if not ws.place_word(word, difficulty):
                    all_placed = False
                    break
            
            if all_placed:
                ws.fill_grid()
                return ws
    
    # If we get here, we couldn't place all words after multiple attempts
    # Try with a larger grid
    ws = WordSearch(words, initial_size + 15)  # Increased fallback size
    ws.fill_grid()
    print("Warning: Could not place all words in the grid. Some words may be missing.")
    return ws

def generate_markdown(ws: WordSearch, difficulty: str) -> str:
    """Generate markdown content for the word search."""
    solution = ws.create_solution_grid()
    
    lines = [
        f"### {difficulty.upper()} SOLUTION",
        '```',
        *[' '.join(cell if cell != ' ' else ' ' for cell in row) for row in solution],
        '```',
        f"\n### {difficulty.upper()} PUZZLE",
        '```',
        *[' '.join(cell if cell != ' ' else '·' for cell in row) for row in ws.grid],
        '```'
    ]
    
    return '\n'.join(lines)

def process_file(input_path: str, output_path: str) -> None:
    """Process input file and generate word search puzzles."""
    with open(input_path, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]
    
    if not words:
        print(f"Warning: {input_path} is empty. Skipping...")
        return
    
    title = Path(input_path).stem
    output = [
        f"# {title.upper()}\n",
        "## WORD BANK\n",
        *[f"- {word}" for word in words],
        "\n---\n"
    ]
    
    # Generate puzzles for each difficulty
    for difficulty in ['easy', 'medium', 'hard']:
        try:
            ws = create_intersecting_word_search(words, difficulty)
            output.append(generate_markdown(ws, difficulty))
            output.extend(['\n'] * 3)  # Add spacing between puzzles
        except Exception as e:
            print(f"Error creating {difficulty} puzzle: {e}")
    
    # Write output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

def main():
    """Main function to process all input files."""
    input_dir = Path("Input")
    output_dir = Path("Output")
    
    # Create directories if they don't exist
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Process each text file in the input directory
    for input_file in input_dir.glob("*.txt"):
        output_file = output_dir / f"{input_file.stem}_wordsearch_intersecting.md"
        print(f"Processing {input_file}...")
        try:
            process_file(str(input_file), str(output_file))
            print(f"Created: {output_file}")
        except Exception as e:
            print(f"Error processing {input_file}: {e}")

if __name__ == "__main__":
    main()
