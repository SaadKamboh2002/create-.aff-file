import aaf2

with aaf2.open('Timeline 1.aaf', 'r') as f:
    print(f.content)  # or explore what the file contains
