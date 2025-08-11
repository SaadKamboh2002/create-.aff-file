import aaf2

with aaf2.open('output.aaf', 'r') as f:
    print(f.content)  # or explore what the file contains
