import sys
from wrapped_json import json

manifest_file = sys.argv[1]

with open(manifest_file, 'r') as f:
    data = json.load(f)
    localhost_idx = data['host_permissions'].index('http://localhost/*')
    del data['host_permissions'][localhost_idx]

    file_idx = data['content_scripts'][0]['matches'].index('file:///*')
    del data['content_scripts'][0]['matches'][file_idx]

    # Delete deepl stuff
    del data['content_scripts'][-1]

    # Background worker is only used for deepl
    del data['background']

    print(json.dumps(data))
