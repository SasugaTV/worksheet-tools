import os
import random
import string
from pathlib import Path
from typing import List, Tuple, Set, Optional

class WordSearch:
    def __init__(self, words: List[str], size: Optional[int] = None):
        self.words = [word.upper().replace(' ', '') for word in words]
        self.longest_word = max(len(word) for word in self.words) if self.words else 0
        self.size = size or max(self.longest_word + 2, 10)  # Minimum size 10x10 for small word lists
        self.grid = [[None for _ in range(self.size)] for _ in range(self.size)]
        self.placed_words = set()
        self.word_positions = []  # Store (word, row, col, dx, dy) for each placed word
        self.directions = {
            'easy': [(0, 1), (1, 0)],  # Right, Down
            'medium': [(0, 1), (1, 0), (1, 1), (1, -1)],  # Right, Down, Diagonal Down-Right, Diagonal Down-Left
            'hard': [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]  # All 8 directions
        }

    def place_word(self, word: str, difficulty: str) -> bool:
        word = word.upper().replace(' ', '')
        if difficulty == 'easy':
            directions = self.directions['easy']
        elif difficulty == 'medium':
            directions = self.directions['medium']
        else:  # hard
            directions = self.directions['hard']
            
        # Try all directions in random order
        directions = random.sample(directions, len(directions))
        
        for direction in directions:
            dx, dy = direction
            # Calculate maximum starting position to fit the word
            max_row = self.size - 1
            max_col = self.size - 1
            
            # Adjust for word length and direction
            if dx > 0:
                max_col -= (len(word) - 1)
            elif dx < 0:
                max_col = len(word) - 1
                
            if dy > 0:
                max_row -= (len(word) - 1)
            elif dy < 0:
                max_row = len(word) - 1
                
            # Ensure we have valid bounds
            if max_row < 0 or max_col < 0 or max_row >= self.size or max_col >= self.size:
                continue
                
            # Try random positions
            positions = [(r, c) for r in range(max_row + 1) for c in range(max_col + 1)]
            random.shuffle(positions)
            
            for row, col in positions[:100]:  # Try up to 100 random positions
                if self.can_place_word(word, row, col, dx, dy):
                    self.do_place_word(word, row, col, dx, dy)
                    return True
                    
        return False

    def can_place_word(self, word: str, row: int, col: int, dx: int, dy: int) -> bool:
        # Check if word fits within grid
        end_row = row + (len(word) - 1) * dy
        end_col = col + (len(word) - 1) * dx
        
        if (end_row < 0 or end_row >= self.size or 
            end_col < 0 or end_col >= self.size):
            return False
            
        # Check each character position
        for i in range(len(word)):
            r = row + i * dy
            c = col + i * dx
            if self.grid[r][c] is not None and self.grid[r][c] != word[i]:
                return False
        return True

    def do_place_word(self, word: str, row: int, col: int, dx: int, dy: int) -> None:
        for i, char in enumerate(word):
            r = row + i * dy
            c = col + i * dx
            self.grid[r][c] = char
        self.placed_words.add(word)
        self.word_positions.append((word, row, col, dx, dy))

    def fill_grid(self):
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] is None:
                    self.grid[i][j] = random.choice(string.ascii_uppercase)

    def create_solution_grid(self) -> List[List[str]]:
        # Create a grid of spaces
        solution = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        
        # Place the actual words in the solution using tracked positions
        for word, row, col, dx, dy in self.word_positions:
            for i, char in enumerate(word):
                r = row + i * dy
                c = col + i * dx
                solution[r][c] = char
        return solution

    def to_markdown(self, difficulty: str) -> str:
        solution = self.create_solution_grid()
        lines = [f"### {difficulty.upper()} SOLUTION"]
        lines.append('```')
        for row in solution:
            lines.append(' '.join(cell if cell is not None else ' ' for cell in row))
        lines.append('```')
        
        lines.append(f"\n### {difficulty.upper()} PUZZLE")
        lines.append('```')
        for row in self.grid:
            lines.append(' '.join(cell for cell in row))
        lines.append('```')
        
        return '\n'.join(lines)

def create_word_search(words: List[str], difficulty: str) -> WordSearch:
    # Process words to remove spaces for length calculation
    processed_words = [word.upper().replace(' ', '') for word in words]
    
    # Start with minimum size based on longest processed word
    min_size = max(len(word) for word in processed_words) + 2
    max_size = min(min_size + 10, 25)  # Increased max size to handle longer words
    
    # Try with increasing grid sizes
    for size in range(min_size, max_size + 1):
        for _ in range(5):  # Try each size up to 5 times
            ws = WordSearch(words, size)
            
            # Try to place all words
            all_placed = True
            for word in words:
                if not ws.place_word(word, difficulty):
                    all_placed = False
                    break
                    
            if all_placed:
                ws.fill_grid()
                return ws
                
    # If we get here, we couldn't place all words
    # Try one last time with a larger grid
    ws = WordSearch(words, max_size + 5)
    for word in words:
        if not ws.place_word(word, difficulty):
            # If still can't place, try with a simpler direction set
            if difficulty == 'hard':
                return create_word_search(words, 'medium')
            elif difficulty == 'medium':
                return create_word_search(words, 'easy')
            raise Exception(f"Failed to place word: {word}")
    
    ws.fill_grid()
    return ws

def process_file(input_path: str, output_path: str) -> None:
    with open(input_path, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f.readlines() if line.strip()]
    
    if not words:
        print(f"Warning: {input_path} is empty. Skipping...")
        return
    
    title = Path(input_path).stem
    output = [f"# {title.upper()}\n"]
    
    # Add word bank
    output.append("## WORD BANK\n")
    output.extend(f"- {word}" for word in words)
    output.append("\n---\n")
    
    # Create puzzles
    for difficulty in ['easy', 'medium', 'hard']:
        try:
            ws = create_word_search(words, difficulty)
            output.append(ws.to_markdown(difficulty))
            output.extend(['\n'] * 3)  # Add three blank lines between puzzles
        except Exception as e:
            print(f"Error creating {difficulty} puzzle: {str(e)}")
    
    # Write to output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print(f"Created: {output_path}")

def main():
    # Define paths
    base_dir = Path(__file__).parent
    input_dir = base_dir / "Input"
    output_dir = base_dir / "Output"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Check if input directory exists
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Error: Input directory '{input_dir}' not found.")
        return
    
    # Get all .txt files in input directory
    input_files = list(input_dir.glob('*.txt'))
    
    if not input_files:
        print(f"No .txt files found in {input_dir}")
        return
    
    # Process each file
    for input_file in input_files:
        output_file = output_dir / f"{input_file.stem}_wordsearch.md"
        process_file(str(input_file), str(output_file))

if __name__ == "__main__":
    main()
