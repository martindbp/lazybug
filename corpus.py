import math
import string
import random
from hanziconv import HanziConv

from merkl import task, FileRef

NON_HANZI_CHARS = [
    '，',
    '！',
    '？',
    '；',
    '：',
    '（',
    '）',
    '［',
    '］',
    '【',
    '】',
    '「',
    '」',
    '﹁',
    '﹂',
    '、',
    '‧',
    '《',
    '》',
    '〈',
    '〉',
    '～ ',
] + list(string.printable[:-6])


@task
def get_corpus(path=FileRef('data/remote/public/models/WeiboSentiment2019.csv'), seed=42):
    random.seed(seed)
    corpus = []
    with open(path, 'r') as f:
        for line in f.readlines():
            text = line.split(',')[-1]
            text = text.replace(' ', '').strip()

            # Split long texts into shorter ones
            texts = []
            max_len = 50
            if len(text) > max_len:
                for i in range(0, len(text)-max_len, max_len):
                    texts.append(text[i:i+max_len])
            else:
                texts.append(text)

            for text in texts:
                if random.random() < 0.1:
                    # Add in some random special characters and ascii
                    random_str = ''.join(random.sample(NON_HANZI_CHARS, k=math.ceil(random.random() * 10)))
                    splice_idx = math.floor(random.random() * len(text))
                    text = text[:splice_idx] + random_str + text[splice_idx:]

                trad = HanziConv.toTraditional(text)
                corpus.append(text)
                corpus.append(trad)

    random.shuffle(corpus)
    return corpus
