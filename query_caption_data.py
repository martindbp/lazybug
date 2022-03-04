import sys
from wrapped_json import json
import glob
from pinyin import normalize_pinyin

query_hz = sys.argv[1]
output_training_data = False
if len(sys.argv) > 2:
    output_training_data = True



def seconds_to_str(s):
    m = int(s // 60)
    s = s - m*60
    return f'{m}:{s}'


for filename in glob.glob('data/remote/public/subtitles/*.json'):
    if filename.endswith('merkl'):
        continue
    with open(filename) as f:
        data = json.load(f)

    lines = data['lines']
    for line in lines:
        words = line[-1]
        if len([w for w in words if w[2] == query_hz or w[4] == query_hz]) > 0:
            if output_training_data:
                print(' '.join(line[0]))
                pys = []
                for (_, _, hz, word_pys, tr) in words:
                    pys.append(''.join(py[1] for py in word_pys))

                print(''.join(pys))
            else:
                print(' '.join(line[0]), line[7], '|', line[8], filename, seconds_to_str(line[1][0]), seconds_to_str(line[2][-1]))
                for (_, _, hz, py, tr) in words:
                    print('\t', hz, py, tr)

    #if not output_training_data:
        #print('')
