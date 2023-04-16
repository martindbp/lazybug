"""
Builds decision tree classifiers for multiple-reading characters

POS = Part Of Speech
PSOS = PartS Of Speech
"""
import re
import os
from pathlib import Path
import numpy as np
from sklearn import tree
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import cross_val_score, LeaveOneOut, StratifiedKFold
from sklearn.metrics import f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import _tree

from han import filter_text_hanzi
from word_disambiguation import pad_parts_of_speech, construct_classifier_args, HANZI_WINDOW_SIZE, POS_WINDOW_SIZE, PSOS

from wrapped_json import json

from merkl import task, IdentitySerializer


def encode_pos_one_hot(pos):
    encoded = np.zeros(len(PSOS), np.float32)

    if pos not in PSOS:
        print(pos, 'not in PSOS')
        #if pos not in PSOS_SINGLE_LETTER_MAP:
        #else:
            #pos = PSOS_SINGLE_LETTER_MAP[pos]

    encoded[PSOS.index(pos)] = 1
    # Also set the label of the leading pos character, e.g. vn is noun-like verb, so also set the verb bit
    encoded[PSOS.index(pos[0])] = 1
    return encoded


def encode_psos_one_hot(psos):
    encoded = np.zeros(len(psos) * len(PSOS), np.float32)
    for i, pos in enumerate(psos):
        encoded[i * len(PSOS) : (i + 1) * len(PSOS)] = encode_pos_one_hot(pos)
    return encoded


def encode_words_one_hot(words, dictionary, dummy_zeros=False):
    encoding = np.zeros(len(dictionary), np.float32)
    if dummy_zeros:
        return encoding

    for word in words:
        if word not in dictionary:
            continue
        encoding[dictionary.index(word)] = 1
    return encoding


HANZI_TOOLS_CL_CHARS = '觉长得还行只系地弹重'


def HANZI_TOOLS_CL(char, prev_psos, curr_pos, next_psos, prev_words, next_words):
    """ https://github.com/peterolson/hanzi-tools/blob/master/src/pinyinify.js """
    afterTag = next_psos[0]
    prevTag = prev_psos[-1]
    if char == "觉":
        if "睡" in prev_words:
            return "jiao4"
        return "jue2"
    elif char == '长':
        if afterTag == "uz":
            return "zhang3"
        if prevTag == "n":
            return "zhang3"
        if prevTag != "d" and afterTag == "ul":
            return "zhǎng"
        return "chang2"
    elif char == '得':
        if prevTag == "v":
            return 'de5'
        if prevTag == "a" or prevTag == "b" or prevTag == "nr":
            return 'de5'
        if afterTag == "ul":
            return "de2"
        if prevTag == "d" or prevTag == "r":
            return "dei3"

        if len(next_words) > 0 and (next_words[0] == "还" or next_words[0] == "還"):
            if next_psos[1][0] in ['r', 'n']:
                return "dei3"
        if afterTag in ['t', 'v', 'p', 'l', 'n']:
            return "dei3"
        return 'de5'
    elif char == "还":
        if '把' in prev_words:
            return "huan2"
        if len(next_words) > 0 and next_words[0] == "有":
            return 'hai2'
        if afterTag[0] in ["r", "n"]:
            return "huan2"
        return 'hai2'
    elif char == "行":
        if prevTag == "m":
            return "hang2"
        return "xing2"
    elif char == "只":
        if prevTag == "m" or afterTag == "n":
            return "zhi1"
        return "zhi3"
    elif char == "系":
        if afterTag == "f" or afterTag[0] == "u":
            return "ji4"
        return "xi4"
    elif char == "地":
        if prevTag == "r":
            return "di4"
        return "de5"
    elif char == "弹":
        nextTags = tag(afterText.join(""))
        if "吉他" in after_words:
            return "tan2"
        if afterTag[0] == "n":
            return "tan2"
        return "dan4"
    elif char == "重":
        if afterTag[0] == "v":
            return "chong2"
        return "zhong4"


def tree_to_function(tree, feature_names, class_labels, function_name):
    tree_ = tree.tree_
    feature_name = [feature_names[i] if i != _tree.TREE_UNDEFINED else "undefined!" for i in tree_.feature]
    function_str = f'def {function_name}(prev_psos, pos, next_psos, prev_words, next_words):\n'

    def recurse(node, depth):
        nonlocal function_str
        indent = "    " * depth
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            name = feature_name[node]
            threshold = tree_.threshold[node]
            function_str += f"{indent}if {name}:\n"
            recurse(tree_.children_right[node], depth + 1)
            function_str += f"{indent}else:\n"
            recurse(tree_.children_left[node], depth + 1)
        else:
            prediction = class_labels[np.argmax(tree_.value[node][0])]
            function_str += f"{indent}return '{prediction}'\n"

    recurse(0, 1)

    exec(function_str, globals())  # puts the function in the local scope
    return globals()[function_name], function_str


@task(serializer=IdentitySerializer)
def train_pinyin_classifiers(pinyin_freq_db):
    readings_all, readings_single = pinyin_freq_db

    skip = [
        '的',  # too many, and noisy
        '了',  # --||--
        '都',  # mislabeled data
    ]

    function_strings = []

    single_readings = {
        '的': 'de5',
        '了': 'le5',
        '都': 'dou1',
    }

    for hz, r in readings_single.items():
        if len(hz) > 1:
            continue

        if hz in skip:
            continue

        if len(r) == 1:
            single_readings[hz] = list(r.keys())[0]
            continue

        distinct_pys = set()
        for py, _ in r.items():
            distinct_pys.add(py)

        if len(distinct_pys) == 1:
            continue

        # Build dictionary
        one_hot_dictionary = []
        for py, examples in r.items():
            for hanzi, i, _, seg_i, segs, _ in examples:
                one_hot_dictionary += [seg[-1] for seg in segs[seg_i - HANZI_WINDOW_SIZE: seg_i]]
                one_hot_dictionary += [seg[-1] for seg in segs[seg_i + 1 : seg_i + 1 + HANZI_WINDOW_SIZE]]

        one_hot_dictionary = sorted(list(set(one_hot_dictionary)))

        # fmt: off
        feature_conditionals = sum(
            [[f"prev_psos[{-o}].startswith('{p}')" for p in PSOS] for o in range(0, POS_WINDOW_SIZE)]
            + [[f"pos.startswith('{p}')" for p in PSOS]]
            + [[f"next_psos[{o}].startswith('{p}')" for p in PSOS] for o in range(0, POS_WINDOW_SIZE)]
            + [[f'"{w}" in prev_words' for w in one_hot_dictionary]]
            + [[f'"{w}" in next_words' for w in one_hot_dictionary]]
        ,[])
        # fmt: on

        data = []
        labels = []
        for py, examples in r.items():
            for hanzi, i, _, seg_i, segs, psos in examples:
                args = construct_classifier_args([s[-1] for s in segs], psos, seg_i)
                if not args:
                    continue
                data.append(args)
                labels.append(py)

        print(hz, len(data))

        classes = sorted(list(set(labels)))
        data_encoded = []
        labels_encoded = []
        for d, l in zip(data, labels):
            try:
                data_encoded.append(
                    np.hstack(
                        [
                            encode_psos_one_hot(d[0] + [d[1]] + d[2]),
                            encode_words_one_hot(d[3], one_hot_dictionary, dummy_zeros=True),
                            encode_words_one_hot(d[4], one_hot_dictionary, dummy_zeros=True),
                        ]
                    )
                )
                labels_encoded.append(classes.index(l))
            except:
                continue

        np_data = np.vstack(data_encoded)
        np_labels = np.array(labels_encoded)

        hanzitools_labels = []
        hanzitools_labels_encoded = []
        if hz in HANZI_TOOLS_CL_CHARS:
            hanzitools_labels = [HANZI_TOOLS_CL(hz, *d) for d, l in zip(data, labels)]
            hanzitools_labels_encoded = [classes.index(l) for l in hanzitools_labels]

        best_clf = None
        best_f1_score = 0
        hanzitools_score = None
        best_depth = None
        for depth in range(1, 6):
            print(depth)
            if len(np_data) > 1000:
                splitter = StratifiedKFold(n_splits=10)
                splitter.get_n_splits(np_data, np_labels)
                splits = splitter.split(np_data, np_labels)
            else:
                splitter = LeaveOneOut()
                splitter.get_n_splits(np_data)
                splits = splitter.split(np_data)
            y_true = []
            y_pred = []
            for train_index, test_index in splits:
                np.random.seed(42)
                if depth == 0:
                    # Train random forest
                    clf = RandomForestClassifier(max_depth=3, random_state=42, n_estimators=20)
                else:
                    clf = tree.DecisionTreeClassifier(max_depth=depth, random_state=42)
                clf = clf.fit(np_data[train_index], np_labels[train_index])

                data_pred = clf.predict(np_data[test_index])
                for pred, label in zip(data_pred, np_labels[test_index]):
                    y_pred.append(pred)
                    y_true.append(label)
            score = f1_score(y_true, y_pred, average='weighted')
            print(f'f1 depth {depth}: {score}')
            if score > best_f1_score:
                best_f1_score = score
                best_clf = clf
                best_depth = depth

        # Fit to all data points
        if best_depth == 0:
            clf = RandomForestClassifier(max_depth=3, random_state=42, n_estimators=20)
        else:
            clf = tree.DecisionTreeClassifier(max_depth=best_depth)

        clf = clf.fit(np_data, np_labels)

        dtree_fun, dtree_str = tree_to_function(clf, feature_conditionals, classes, hz)
        function_strings.append(dtree_str)

        dtree_labels = [dtree_fun(*d) for d, l in zip(data, labels)]
        dtree_labels_encoded = [classes.index(l) for l in dtree_labels]

        y_pred_all = clf.predict(np_data)
        all_data_score = f1_score(y_true, y_pred_all, average='weighted')
        print(f'best f1 depth {best_depth}: {best_f1_score}')
        print(f'best f1 depth {best_depth} all data: {all_data_score}')
        print('f1 de: ', f1_score(y_true, dtree_labels_encoded, average='weighted'))
        if hz in HANZI_TOOLS_CL_CHARS:
            print(
                'f1 hanzitools: ', f1_score(y_true, hanzitools_labels_encoded, average='weighted'),
            )

        max_score = 0
        for c in range(7):
            score = f1_score(y_true, c * np.ones(len(y_true)), average='weighted')
            if score > max_score:
                max_score = score

        print('same f1: ', max_score)

    out_code = ''
    out_code += f'HANZI_WINDOW_SIZE = {HANZI_WINDOW_SIZE}\n\n'
    out_code += f'POS_WINDOW_SIZE = {POS_WINDOW_SIZE}\n\n'
    out_code += '\n\n'.join(function_strings)
    out_code += f'single_readings = {json.dumps(single_readings)}'
    return out_code


def exec_code(code):
    exec_locals = {}
    exec(code, None, exec_locals)
    return exec_locals
