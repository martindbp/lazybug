import yaml
import glob
import numpy as np
from collections import defaultdict
from sentence_transformers import SentenceTransformer

from merkl import task, batch, pipeline, FileRef, Eval

model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L6-v2')

@task
def embed_sentence(sentence):
    raise NotImplementedError
    return 'embedding'


@batch(embed_sentence)
def embed_sentences(sentences):
    embeddings = model.encode(sentences)
    return [embeddings[i, :] for i in range(embeddings.shape[0])]


@task
def get_sentences_similarity(sentences_embeddings):
    embeddings = np.stack(sentences_embeddings)
    # Normalize to unit length
    norms = np.linalg.norm(embeddings, axis=1)
    embeddings = embeddings / norms[:, np.newaxis]
    cosine_similarity = embeddings @ embeddings.T
    return cosine_similarity


@task
def get_all_words(caption_files):
    words = defaultdict(set)
    all_translations = []
    for final_caption_file in caption_files:
        with open(final_caption_file, 'r') as f:
            data = yaml.load(f)
        lines = data['lines']
        for line in lines:
            w = line[-1]
            for (_, _, hz, py, tr) in w:
                words[f'{hz}-{py}'].add(tr)
                all_translations.append(tr)

    all_translations = list(set(all_translations))
    with Eval():
        embed_sentences(all_translations)  # trigger the calculation and cache

    for hz in words.keys():
        words[hz] = list(words[hz])

    return words


@task(serializer=yaml)
def get_embeddings_file(words):
    out_yaml = []
    for hz_py, translations in words.items():
        if len(translations) <= 1:
            continue

        with Eval():
            embeddings = embed_sentences(translations)
        similarity_matrix = get_sentences_similarity(embeddings).eval()
        out_yaml.append((hz_py, translations, similarity_matrix.tolist()))
    return out_yaml


def similarity_pipeline():
    # Go through all final captions, save all words and their list of possible translations
    final_caption_files = [
        FileRef(p) for p in glob.glob('data/remote/public/subtitles/*.json') if not str(p).endswith('merkl')
    ]

    words = get_all_words(final_caption_files)
    embeddings = get_embeddings_file(words)
    embeddings > 'data/public/translation_similarity.json'
    return embeddings
