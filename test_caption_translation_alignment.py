import io
import json
import unittest
import webvtt
from caption_translation_alignment import align_translations_and_captions, timestamp_to_seconds, make_caption_lines_lists


def print_data(caption_data, translations):
    for i, t in enumerate(translations):
        print(i, t.text, timestamp_to_seconds(t.start), timestamp_to_seconds(t.end))

    for i, c in enumerate(caption_data['lines']):
        print(i, c[:3])


class TestAlignment(unittest.TestCase):

    def test_alignment(self):
        with open('data/remote/private/backup/caption_data/raw_captions/youtube-YtzqsA-a8MM.json', 'r') as f:
            caption_data_orig = json.load(f)

        translations_orig = webvtt.read('data/remote/private/backup/caption_data/translations/youtube-YtzqsA-a8MM.en.vtt')

        print_data(caption_data_orig, translations_orig)

        caption_data = dict(caption_data_orig)
        translations = list(translations_orig)
        caption_data['lines'] = caption_data['lines'][159+2:170-6]
        make_caption_lines_lists(caption_data['lines'])
        translations = translations[149+2:160-6]
        print_data(caption_data, translations)
        aligned_translations = align_translations_and_captions(caption_data, translations, remove_unmatched_captions=False)
        self.assertEqual(len(caption_data['lines']), 2)
        self.assertEqual(len(aligned_translations), 2)

        caption_data = dict(caption_data_orig)
        translations = list(translations_orig)
        caption_data['lines'] = caption_data['lines'][411-10:415+30]
        make_caption_lines_lists(caption_data['lines'])
        translations = translations[388-10:392+30]
        print_data(caption_data, translations)
        aligned_translations = align_translations_and_captions(caption_data, translations, remove_unmatched_captions=False)


if __name__ == '__main__':
    unittest.main()
