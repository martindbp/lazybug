import os
import sys
from wrapped_json import json
import pyperclip

CHAR_LIMIT = float('inf')

if os.path.exists(sys.argv[1]):
    ids_path = sys.argv[1]
    with open(ids_path, 'r') as f:
        ids = [l for l in f.read().strip().split('\n')]
else:
    ids = [sys.argv[1]]

for video_id in ids:
    video_id = f'youtube-{video_id}'
    with open(f'data/remote/private/backup/caption_data/raw_captions/{video_id}.json', 'r') as f:
        data = json.loads(f.read())

    lines = data['lines']
    """
    if len(sys.argv) == 3:
        for text, t0, t1, rect, *_ in lines:
            print(text)
        sys.exit()
    """

    out_file = f'data/remote/private/backup/caption_data/machine_translations/{video_id}.txt'
    if os.path.exists(out_file):
        with open(out_file, 'r') as f:
            out_lines = [line for line in f.read().strip().split('\n')]
            if len(out_lines) == len(lines):
                print(f'{video_id} already done')
                continue


    num_printed_chars = 0
    accumulated_lines = []
    translation_lines = []
    for i, (text, t0, t1, rect, *_) in enumerate(lines):
        if num_printed_chars + len(text) + 1 > CHAR_LIMIT or i == len(lines) - 1:
            if i == len(lines) - 1:
                accumulated_lines.append(text)

            print('\n'.join(accumulated_lines))
            print('\nLines have been copied to clipboard')
            pyperclip.copy('\n'.join(accumulated_lines))
            print("\nPaste the translation here:\n")
            input_translation_lines = []
            try:
                while True:
                    input_translation_lines.append(input())
            except KeyboardInterrupt:
                pass
            print('')

            translation_lines += input_translation_lines
            accumulated_lines = []
            num_printed_chars = 0

        accumulated_lines.append(text)
        num_printed_chars += len(text) + 1  # 1 for newline

    if len(translation_lines) != len(lines):
        breakpoint()

    with open(out_file, 'w') as f:
        translation_lines = "\n".join(translation_lines)
        f.write(translation_lines)
