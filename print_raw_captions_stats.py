import os
from wrapped_json import json
import glob

print('filename \t\t\t n_l \t mean_l  max_l')
total_num_chars = 0
total_num_sentences = 0
for filename in glob.glob('data/remote/private/backup/caption_data/raw_captions/*.json'):
    if filename.endswith('merkl'):
        continue

    with open(filename, 'r') as f:
        data = json.loads(f.read())

    lines = data['lines']
    basename = os.path.basename(filename)
    if len(lines) == 0:
        print(f'{basename} NO LINES!!!')
        continue

    num_chars = 0
    max_len = 0
    #num_zero = 0
    #first_zero = 0
    for texts, t0s, t1s, *_ in lines:
        text_len = len(''.join(texts)) if isinstance(texts, list) else len(texts)
        num_chars += text_len
        max_len = max(max_len, text_len)
        #t0 = t0s[0]
        #t1 = t1s[len(t1s)]
        #if t0 == 0 or t1 == 0:
            #num_zero += 1
            #if first_zero == 0:
                #first_zero = max(t0, t1)

    total_num_chars += num_chars
    total_num_sentences += len(lines)
    #if num_zero > 0:
        #print(f'WARNING: {num_zero} lines with t0/t1 == 0.0, first seen at {first_zero}')

    print(f'{basename} \t {len(lines)} \t {num_chars / len(lines):.2f} \t {max_len}')

print(f'Total num chars: {total_num_chars}')
print(f'Total num sentences: {total_num_sentences}')
