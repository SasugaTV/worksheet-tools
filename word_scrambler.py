import os
import random
from pathlib import Path

def scramble_word(word):
    """Scramble the characters in a word randomly."""
    chars = list(word.lower())
    random.shuffle(chars)
    return ''.join(chars)

def process_file(input_path, output_path):
    """Process a single input file and create a scrambled output file."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        if not lines:
            print(f"Warning: {input_path} is empty. Skipping...")
            return
            
        # Get filename without extension for the title
        title = Path(input_path).stem
        
        # Generate scrambled lines
        scrambled_lines = [scramble_word(line) for line in lines]
        
        # Prepare output content
        output_content = [
            f"# {title.upper()}\n",
            "## WORD BANK\n"
        ]
        
        # Add original words with numbers
        output_content.extend(f"{i+1}. {line}" for i, line in enumerate(lines))
        
        # Add scrambled section
        output_content.extend([
            "\n## UNSCRAMBLE THE WORDS\n"
        ])
        
        # Add scrambled words with numbers
        output_content.extend(f"{i+1}. {scrambled_line}" for i, scrambled_line in enumerate(scrambled_lines))
        
        # Write to output file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_content))
            
        print(f"Created: {output_path}")
        
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")

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
        output_file = output_dir / f"{input_file.stem}_wordscrambler.md"
        process_file(input_file, output_file)

if __name__ == "__main__":
    main()
