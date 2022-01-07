import os
import sys
import glob
from wrapped_json import json

from levenshtein import weighted_levenshtein, OpType

default = None
if len(sys.argv) > 1:
    # If default is True, then all changes are considered to be correct, otherwise considered to be incorrect
    default = sys.argv[1] == '1'

printed_lines = set()
printed_line_words = set()

def print_caption(i, j, caption_file, test_line, line):
    if i not in printed_lines:
        t = test_line[1][0]
        t_m = int(t // 60)
        t_s = t - t_m*60
        print('')
        print(caption_file + f' {t_m}:{t_s:.1f}')
        print(' '.join(test_line[0]))
        printed_lines.add(i)

        if j is None:
            print('Segmentation error')
            print('Test: ', ' '.join([w[2] for w in test_line[9]]))
            print('New: ', ' '.join([w[2] for w in line[9]]))

    if j is not None:
        if f'{i}-{j}' not in printed_line_words:
            word = line[9][j]
            print(word)
            printed_line_words.add(f'{i}-{j}')


do_quit = False

num_correct_tr, num_incorrect_tr = 0, 0
num_correct_py, num_incorrect_py = 0, 0
num_segmentation_errors = 0

for filename in glob.glob('data/remote/private/backup/caption_data/test/*.json'):
    with open(filename, 'r') as f:
        test_data = json.load(f)

    test_lines = test_data['lines']

    caption_file = os.path.basename(filename)
    with open(f'data/remote/public/subtitles/final_captions/{caption_file}') as f:
        data = json.load(f)

    lines = data['lines']

    for i, (test_line, line) in enumerate(zip(test_lines, lines)):
        test_words = test_line[9]
        words = line[9]
        _, ops = weighted_levenshtein(
            [w[2] for w in words],
            [w[2] for w in test_words],
            return_ops=True
        )

        is_segmentation_error = False
        for op in ops:
            if op.type != OpType.SUBSTITUTE:
                is_segmentation_error = True
                break
            else:
                test_word = test_words[op.to_idx]
                word = words[op.from_idx]
                if test_word[2] != word[2]:
                    is_segmentation_error = True
                    break

            test_py, test_tr = test_word[-2:]
            py, tr = word[-2:]
            has_py_test = isinstance(test_py, list)
            if not isinstance(test_tr, list):
                test_tr = [test_tr, [], []]  # unknown, [correct], [incorrect]#, [maybe]
            if not isinstance(test_py, list):
                test_py = [test_py, 'unknown']

            if py != test_py[0]:
                print_caption(i, op.to_idx, caption_file, test_line, line)
                if test_py[1] == 'unknown':
                    print(f'Pinyin differs: {py} instead of {test_py[0]}')
                    print(f'1. {py} is correct')
                    print(f'2. {test_py[0]} is correct')
                    print('3. neither is correct')
                    while True:
                        if default is not None:
                            choice = '1' if default else '2'
                        else:
                            choice = input()
                        unknown_option = False
                        if choice == '1':
                            test_py = [py, 'correct']
                        elif choice == '2':
                            test_py = [test_py[0], 'correct']
                        elif choice == '3':
                            test_py = [test_py[0], 'incorrect']
                        elif choice == 'q':
                            do_quit = True
                            break
                        else:
                            print('Unknown option')
                            unknown_option = True

                        if not unknown_option:
                            break
                elif test_py[1] == 'correct':
                    print(f'Pinyin incorrect: {py} instead of {test_py[0]}')
                    num_incorrect_py += 1
                elif test_py[1] == 'incorrect':
                    print_caption(i, op.to_idx, caption_file, test_line, line)
                    print(f'Both pinyin incorrect: {py} and {test_py[0]}')
                    num_incorrect_py += 1

                # Replace with new test py
                test_word[-2] = test_py
            else:
                if has_py_test:
                    num_correct_py += 1

            test_tr_unk, test_tr_correct, test_tr_incorrect = test_tr
            if tr in test_tr_incorrect:
                print_caption(i, op.to_idx, caption_file, test_line, line)
                print(f'Still incorrect translation: {tr}')
                num_incorrect_tr += 1
            elif len(test_tr_correct) > 0 and tr not in test_tr_correct:
                print_caption(i, op.to_idx, caption_file, test_line, line)
                print(f'Differing translation: {tr} instead of {test_tr_correct}')
                print(f'1. {tr} is also correct')
                print(f'2. {tr} is incorrect')
                while True:
                    if default is not None:
                        choice = '1' if default else '2'
                    else:
                        choice = input()
                    unknown_option = False
                    if choice == '1':
                        test_tr_correct.append(tr)
                    elif choice == '2':
                        test_tr_incorrect.append(tr)
                    elif choice == 'q':
                        do_quit = True
                        break
                    else: 
                        print('Unknown option')
                        unknown_option = True

                    if not unknown_option:
                        break
            elif test_tr_unk is not None and tr != test_tr_unk:
                print_caption(i, op.to_idx, caption_file, test_line, line)
                print(f'New translation: {tr} instead of unknown {test_tr_unk}')
                print('1. Both are correct')
                print('2. Both are wrong')
                print(f'3. {tr} is correct, {test_tr_unk} is wrong')
                print(f'4. {test_tr_unk} is correct, {tr} is wrong')
                while True:
                    if default is not None:
                        if default == False:
                            print('Cant decide between optoins 2 and 4')
                            sys.exit(1)
                        choice = '3'
                    else:
                        choice = input()
                    unknown_option = False
                    if choice == '1':
                        test_tr_correct.append(tr)
                        test_tr_correct.append(test_tr_unk)
                    elif choice == '2':
                        test_tr_incorrect.append(tr)
                        test_tr_incorrect.append(test_tr_unk)
                    elif choice == '3':
                        test_tr_correct.append(tr)
                        test_tr_incorrect.append(test_tr_unk)
                    elif choice == '4':
                        test_tr_incorrect.append(tr)
                        test_tr_correct.append(test_tr_unk)
                    elif choice == 'q':
                        do_quit = True
                        break
                    else: 
                        print('Unknown option')
                        unknown_option = True

                    if not unknown_option:
                        break

                test_word[-1] = [None, test_tr_correct, test_tr_incorrect]
            elif test_tr_unk is None and tr not in test_tr_correct and tr not in test_tr_incorrect:
                print_caption(i, op.to_idx, caption_file, test_line, line)
                print(f'New translation: {tr} (all other examples are incorrect)')
                print(f'1. {tr} is correct')
                print(f'2. {tr} is incorrect')

                while True:
                    if default is not None:
                        choice = '1' if default else '2'
                    else:
                        choice = input()
                    unknown_option = False
                    if choice == '1':
                        test_tr_correct.append(tr)
                    elif choice == '2':
                        test_tr_incorrect.append(tr)
                    elif choice == 'q':
                        do_quit = True
                        break
                    else: 
                        print('Unknown option')
                        unknown_option = True

                    if not unknown_option:
                        break

                test_word[-1] = [None, test_tr_correct, test_tr_incorrect]
            elif tr in test_tr_correct:
                num_correct_tr += 1


            if do_quit:
                break

        if is_segmentation_error:
            if len(test_line) > 10:
                incorrect_segmentations = test_line[10]
            else:
                incorrect_segmentations = []
            print_caption(i, None, caption_file, test_line, line)
            num_segmentation_errors += 1
            new_segmentation = ' '.join([w[2] for w in line[9]])
            test_segmentation = ' '.join([w[2] for w in test_line[9]])
            if new_segmentation not in incorrect_segmentations:
                print(f'1. New segmentation is correct')
                print(f'2. New segmentation is incorrect')
                while True:
                    if default is not None:
                        choice = '1' if default else '2'
                    else:
                        choice = input()
                    unknown_option = False
                    if choice == '1':
                        incorrect_segmentations.append(test_segmentation)
                        test_lines[i] = [*lines[i], incorrect_segmentations]
                    elif choice == '2':
                        if len(test_lines[i]) > 10:
                            test_lines[i][10].append(new_segmentation)
                        else:
                            test_lines[i].append([new_segmentation])
                    elif choice == 'q':
                        do_quit = True
                        break
                    else: 
                        print('Unknown option')
                        unknown_option = True

                    if not unknown_option:
                        break
        if do_quit:
            break


    #print('Writing back test file')
    with open(filename, 'w') as f:
        test_data = json.dump(test_data, f)

print('\n=================================')
print('Num correct py', num_correct_py)
print('Num incorrect py', num_incorrect_py)
print('Num correct tr', num_correct_tr)
print('Num incorrect tr', num_incorrect_tr)
print('Num segmentation errors', num_segmentation_errors)
