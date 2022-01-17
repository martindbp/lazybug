import os
import sys
from wrapped_json import json
from pinyin import normalized_to_diacritical

# Add a test case
commit_as_correct = False
if len(sys.argv) == 5:
    video_id, time, hz, py = sys.argv[1:]
    py = normalized_to_diacritical(py)
elif len(sys.argv) == 4:
    py = None
    video_id, time, hz = sys.argv[1:]
elif len(sys.argv) == 3:
    py = None
    hz = None
    commit_as_correct = True
    video_id, time = sys.argv[1:]


minutes, seconds = time.split(':')
minutes = int(minutes)
seconds = float(seconds)
time = seconds + 60*minutes


with open(f'data/remote/private/caption_data/test/{video_id}.json') as f:
    data = json.load(f)

lines = data['lines']

for line in lines:
    words = line[-1]
    line_hz = ' '.join(line[0])
    for i in range(len(line[0])):
        t0 = line[1][i]
        t1 = line[2][i]
        if t0 <= time <= t1:
            print('Before', words)
            for i, (_, _, word_hz, word_py, tr) in enumerate(words):
                if word_hz != hz:
                    if not isinstance(word_py, list):
                        words[i][-2] = [word_py, 'correct']
                    if not isinstance(tr, list):
                        words[i][-1] = [None, [tr], []]
                    continue

                if py is not None and word_py != py:
                    print(f'Setting {py} as as correct pinyin')
                    words[i][-2] = [py, 'correct']

                if py is None:
                    if isinstance(tr, list):
                        if len(tr[1]) > 0:
                            words[i][-1] = [None, [], [tr[1][0]]]
                        elif tr[0] is not None:
                            words[i][-1] = [None, [], [tr[0]]]
                    else:
                        print(f'Setting {tr} as wrong translation')
                        words[i][-1] = [None, [], [tr]]
                    if not isinstance(word_py, list):
                        words[i][-2] = [word_py, 'correct']

                break
            #print('After', words)


if input(f'Commit changes{" as correct" if commit_as_correct else ""}? Y/n: ') == 'Y':
    with open(f'data/remote/private/caption_data/test/{video_id}.json', 'w') as f:
        json.dump(data, f)
else:
    print('Aborting...')

