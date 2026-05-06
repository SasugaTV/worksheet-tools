import os
import random
from pathlib import Path
from typing import List, Tuple, Dict

def generate_missing_letters(word: str, difficulty: str) -> Tuple[str, str]:
    """Generate a word with missing letters and return (puzzle, solution)."""
    word = word.upper()
    length = len(word)
    
    if length <= 2:
        return ('_' * length, word)
    
    # Determine how many letters to remove based on word length and difficulty
    if difficulty == 'easy':
        # Remove 1-2 letters, keep first and last
        num_to_remove = min(2, max(1, length // 4))
        keep = {0, length-1}  # Keep first and last letters
    elif difficulty == 'medium':
        # Remove about 1/3 of letters, keep first
        num_to_remove = max(1, length // 3)
        keep = {0}  # Keep only first letter
    else:  # hard
        # Remove about 1/2 of letters, no guarantees
        num_to_remove = max(1, length // 2)
        keep = set()
    
    # Ensure we don't remove too many letters
    num_to_remove = min(num_to_remove, length - len(keep))
    
    # Choose positions to blank out (not in keep set)
    positions = [i for i in range(length) if i not in keep]
    to_remove = random.sample(positions, min(num_to_remove, len(positions)))
    
    # Create the puzzle and solution
    puzzle = []
    solution = []
    for i, char in enumerate(word):
        if i in to_remove:
            puzzle.append('_')
            solution.append(char)
        else:
            puzzle.append(char)
            solution.append(' ')
    
    return (' '.join(puzzle), ' '.join(solution))

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
    
    # Create puzzles for each difficulty
    for difficulty in ['easy', 'medium', 'hard']:
        output.append(f"## {difficulty.upper()} MISSING LETTERS\n")
        output.append("Fill in the missing letters in each word.\n")
        
        # Create puzzle and solution
        for word in words:
            puzzle, solution = generate_missing_letters(word, difficulty)
            output.append(f"- {puzzle}")
        
        output.append("\n### SOLUTIONS\n")
        for word in words:
            puzzle, solution = generate_missing_letters(word, difficulty)
            output.append(f"- {word.upper()}: {solution}")
        
        output.extend(['\n'] * 3)  # Add three blank lines between difficulties
    
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
        output_file = output_dir / f"{input_file.stem}_missingletters.md"
        process_file(str(input_file), str(output_file))

if __name__ == "__main__":
    main()
