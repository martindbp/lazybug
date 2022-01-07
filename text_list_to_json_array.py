import sys
import json

lines = []
for line in sys.stdin:
    lines.append(line.strip())

print(json.dumps(lines))
