import os
import random
from pathlib import Path
from typing import List, Tuple, Dict

def split_word(word: str) -> Tuple[str, str]:
    """Split a word into two halves."""
    mid = (len(word) + 1) // 2  # Prefer first half to be longer for even splits
    return word[:mid], word[mid:]

def generate_word_split_worksheet(words: List[str]) -> str:
    """Generate a markdown worksheet for matching word halves."""
    # Split words and create pairs
    word_pairs = [split_word(word.lower()) for word in words]
    
    # Sort first halves alphabetically
    word_pairs.sort(key=lambda x: x[0])
    first_halves = [pair[0] for pair in word_pairs]
    
    # Get second halves and shuffle them
    second_halves = [pair[1] for pair in word_pairs]
    random.shuffle(second_halves)
    
    # Create the worksheet content
    content = [
        "# Word Split Match\n",
        "## INSTRUCTIONS\n",
        "Draw a line to match the beginning of each word with its correct ending.\n",
        "## MATCH THE WORD HALVES\n",
        "| First Half | Second Half |",
        "|------------|-------------|"
    ]
    
    # Add word halves to the table
    for first, second in zip(first_halves, second_halves):
        content.append(f"| {first.ljust(10)} | {second.ljust(10)} |")
    
    # Add solutions section
    content.extend([
        "\n---\n",
        "## SOLUTIONS\n",
        "Check your answers below.\n",
        "| Complete Word |",
        "|---------------|"
    ])
    
    # Add solutions
    for first, second in word_pairs:
        content.append(f"| {first + second} |")
    
    return '\n'.join(content)

def process_input_files():
    """Process all .txt files in the Input directory."""
    # Create directories if they don't exist
    input_dir = Path("Input")
    output_dir = Path("Output")
    output_dir.mkdir(exist_ok=True)
    
    # Process each text file in the input directory
    for input_file in input_dir.glob("*.txt"):
        # Read words from input file
        with open(input_file, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        
        if not words:
            print(f"No words found in {input_file.name}")
            continue
        
        # Generate worksheet content
        worksheet = generate_word_split_worksheet(words)
        
        # Write to output file
        output_file = output_dir / f"{input_file.stem}_wordsplit.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(worksheet)
        
        print(f"Created: {output_file}")

if __name__ == "__main__":
    process_input_files()
