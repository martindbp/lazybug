import os
import sys
from wrapped_json import json


for filename in sys.argv[1:]:
    if filename.endswith('merkl'):
        pass
        #new_name = filename[:-10] + 'json.merkl'
        #print(f'Renaming {filename} -> {new_name}')
        #os.rename(filename, new_name)
    else:
        print(f'Writing json to {filename}')
        with open(filename, 'r') as f:
            data = json.load(f)

        #new_filename = filename[:-4] + 'json'
        with open(filename, 'w') as new_f:
            json.dump(data, new_f)

        #print(f'Removing {filename}')
        #os.remove(filename)
