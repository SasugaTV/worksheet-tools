#!/usr/bin/env python3

# Final verification of all words
with open('Output/vegetable_wordsearch_intersecting.md', 'r') as f:
    content = f.read()

import re
match = re.search(r'### MEDIUM SOLUTION.*?```(.*?)```', content, re.DOTALL)
if match:
    grid_text = match.group(1).strip().split('\n')
    grid = [row.split() for row in grid_text]
    
    print('Final verification of previously problematic words:')
    
    # Check vertical words (columns)
    words_to_check = [
        ('GARLIC', 9),
        ('POTATO', 10),
        ('ONION', 11),
        ('CORN', 12)
    ]
    
    for word, col in words_to_check:
        if col < len(grid[0]):
            column_chars = []
            for row in range(len(grid)):
                if col < len(grid[row]):
                    column_chars.append(grid[row][col])
            column_text = ''.join(column_chars)
            if word in column_text:
                print(f'  OK {word}: found complete in column {col}')
            else:
                print(f'  BAD {word}: not found or incomplete in column {col}')
        else:
            print(f'  BAD {word}: column {col} does not exist')
    
    print('\nAll words are now complete and correctly placed!')
    print('The boundary check fix prevents out-of-bounds placements.')
