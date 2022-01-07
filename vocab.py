import string
from collections import defaultdict
from functools import cached_property

import torch
import numpy as np
from merkl import task, FileRef, Eval

from corpus import get_corpus, NON_HANZI_CHARS


def extract_child_components(cid, links):
    components = []
    for to_cid in links.get(cid, []):
        components.append(to_cid)
        components += extract_child_components(to_cid, links)

    return components


@task
def load_components_and_links(path):
    counts = defaultdict(lambda: 0)

    # First load all the links, and get the use count of each component
    links = defaultdict(list)
    components = []
    with open(path, 'r') as f:
        for k, line in enumerate(f):
            line = line.strip()
            from_cjk_id, rest = line.split(':')
            _type = rest[: rest.index('(')]
            if _type.startswith('m'):
                # It's a modification of another char, but we're
                # only interested in composition
                continue

            cjk_links = rest[rest.index('(') + 1 : -1].split(',')
            for to_cjk_id in cjk_links:
                if to_cjk_id == '':
                    continue
                links[from_cjk_id].append(to_cjk_id)

            components.append(from_cjk_id)

    flat_links = defaultdict(list)
    for from_cid in links:
        flat_links[from_cid] = extract_child_components(from_cid, links)

    return components, flat_links


@task
def get_vocab_links_and_weights(corpus, components, links, vocab_size=512):
    component_counts = defaultdict(lambda: 1)  # 1 so we don't get divide by zero
    total_examples = 0
    for i, text in enumerate(corpus):
        if i % 10000 == 0:
            print(f'{100 * i / len(corpus):.2f}%')

        for char in text:
            total_examples += 1
            component_counts[char] += 1
            for to_cid in links.get(char, []):
                component_counts[to_cid] += 1

    sorted_component_counts = list(reversed(sorted(component_counts.items(), key=lambda x: x[1])))
    vocab = [char for char, _ in sorted_component_counts[:vocab_size]]

    # Add all printable (ascii) characters
    for c in string.printable[:-6]:
        vocab.append(c)

    # Add Chinese punctuation
    vocab = vocab + NON_HANZI_CHARS
    vocab = list(set(vocab))  # dedupe in case special characters already in vocab

    vocab_count = np.ones(len(vocab), dtype=float)
    for i, component in enumerate(vocab):
        vocab_count[i] = component_counts[component]
        if component_counts[component] == 1:
            print(f'Component {component} has no count')

    vocab_weights = total_examples / vocab_count
    return vocab, vocab_weights


class Vocab:
    def __init__(self, cjk_decomp_path=FileRef('data/git/cjk-decomp.txt'), component_vocab_size=1024):
        self.cjk_decomp_path = cjk_decomp_path
        self.component_vocab_size = component_vocab_size

    def load(self):
        with Eval():
            self.components, self.links = load_components_and_links(self.cjk_decomp_path)
            self.vocab, self._weights = get_vocab_links_and_weights(
                get_corpus(), self.components, self.links, self.component_vocab_size
            )
            self.vocab_size = len(self.vocab)

        self._post_load()

    def _post_load(self):
        self.vocab_set = set(self.vocab)
        self.component_vocab_index = {char: i for i, char in enumerate(self.vocab)}

    def set_device(self, device):
        self.device = device

    def encode_char_components(self, char):
        encoded = np.zeros((len(self.vocab)), dtype=float)
        if char in self.vocab:
            if char in self.vocab_set:
                encoded[self.component_vocab_index[char]] = 1

        for link in self.links.get(char, []):
            if link in self.vocab_set:
                encoded[self.component_vocab_index[link]] = 1

        return encoded

    @cached_property
    def weights(self):
        # On average, for each real character we have an empy one between, plus as many as the characters on the side
        factor = 3
        return torch.from_numpy(self._weights * factor).to(self.device)

    def __len__(self):
        return self.vocab_size

    def __getstate__(self):
        return {
            'vocab': self.vocab,
            'links': self.links,
            '_weights': self._weights,
            'vocab_size': self.vocab_size,
        }

    def __setstate__(self, state):
        self.vocab = state['vocab']
        self.links = state['links']
        self.vocab_size = state['vocab_size']
        self._weights = state['_weights']
        self._post_load()
