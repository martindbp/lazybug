import re
from typing import *
from levenshtein import weighted_levenshtein

HANZI_WINDOW_SIZE = 10
POS_WINDOW_SIZE = 2

PSOS = [
    '^',  # sentence start
    '$',  # sentence end
    '_',  # before or after start/end
    'A', 'C', 'Caa', 'Cab', 'Cba', 'Cbb', 'D', 'Da', 'DE', 'Dfa', 'Dfb', 'Di', 'Dk',
    'F', 'FW', 'I', 'N', 'Na', 'Nb', 'Nc', 'Ncd', 'Nd', 'Nep', 'Neqa', 'Neqb', 'Nes',
    'Neu', 'Nf', 'Ng', 'Nh', 'Nv', 'P', 'S', 'SHI', 'T', 'V', 'VA', 'VAC', 'VB', 'VC',
    'VCL', 'VE', 'VD', 'VF', 'VG', 'VH', 'VHC', 'VI', 'VJ', 'VK', 'VL', 'V_2',
    'Q',
]

PSOS_MAP_TO_Q = [
    'QUESTIONCATEGORY',
    'DASHCATEGORY',
    'PARENTHESISCATEGORY',
    'PERIODCATEGORY',
    'EXCLAMATIONCATEGORY',
    'COMMACATEGORY',
    'WHITESPACE',
    'PAUSECATEGORY',
    'SEMICOLONCATEGORY',
    'COLONCATEGORY',
    'ETCCATEGORY',
]



def pad_parts_of_speech(psos: List[str], size: int):
    return (size - 1) * ['_'] + ['^'] + psos + ['$'] + (size - 1) * ['_']


def map_psos(psos):
    psos_mapped = []
    for pos in psos:
        if pos in PSOS_MAP_TO_Q:
            psos_mapped.append('Q')
        else:
            psos_mapped.append(pos)
    return psos_mapped


def construct_classifier_args(hzs, psos, idx):
    psos = map_psos(psos)
    psos_padded = pad_parts_of_speech(psos, POS_WINDOW_SIZE)
    idx_padded = idx + POS_WINDOW_SIZE
    psos_padded_cropped = psos_padded[idx_padded - POS_WINDOW_SIZE : idx_padded + POS_WINDOW_SIZE + 1]

    if len(psos_padded_cropped) != 1 + 2 * POS_WINDOW_SIZE:
        # Could be a sentence shorter than specified size
        return None

    return (
        psos_padded_cropped[:POS_WINDOW_SIZE],
        psos[idx],
        psos_padded_cropped[POS_WINDOW_SIZE + 1 :],
        hzs[idx - HANZI_WINDOW_SIZE : idx],
        hzs[idx + 1 : idx + 1 + HANZI_WINDOW_SIZE],
    )
